from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import ListView

from app.helpers import base_post_method
from app.mixins import ViewWitsContext
from app.models import Notification
from community.forms import CreateCommunityForm, BlackListForm
from community.models import Community, CommunityFollowers, CommunityFollowRequests
from core.decorators import owner_required
from users.forms import PublishForm
from users.models import Moderators, Publication


class CommunityView(ViewWitsContext):
    template_name = "community/community_detail/community_main_page.html"

    def get_context_data(self, request, **kwargs):
        context = super().get_context_data(request, **kwargs)
        name = self.kwargs.get("name")
        community_data = Community.objects.get(name=name)

        # PUBLICATION DATA
        author_id = community_data.admins.get(is_owner=True).user.id
        publication_form = PublishForm(initial={"author_id": author_id})
        is_owner = Moderators.objects.filter(user=self.request.user, is_owner=True).exists()

        # FOLLOWERS DATA
        community_followers = CommunityFollowers.objects.filter(community=community_data, is_follow=True).all()
        is_follow_user = CommunityFollowers.objects.filter(
            community=community_data, is_follow=True, user=self.request.user.id
        ).all()
        request_status = CommunityFollowRequests.objects.filter(
            community=community_data, user=self.request.user.id
        ).all()

        # CONTEXT
        context["publication_form"] = publication_form
        context["name"] = name
        context["community_data"] = community_data
        context["community_followers"] = community_followers
        context["is_follow_user"] = is_follow_user
        context["request_status"] = request_status
        context["is_owner"] = is_owner
        context["author_id"] = author_id
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        context["follow_value"] = "Unfollow" if context["is_follow_user"].exists() else "Follow"
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        community = context["community_data"]
        action = self.request.POST.get("action")

        # FOLLOW REQUESTS
        if action == "follow" or action == "unfollow":
            return self.handle_follow_action(context)
        elif action == "send_request" or action == "remove_request":
            request_obj = CommunityFollowRequests.objects.filter(
                community=context["community_data"], user=self.request.user.id, send_status=True
            )
            if request_obj.exists():
                request_obj.delete()
                return JsonResponse({"success": True})
            else:
                return self.handle_send_request_action(context)

        # POST CREATION REQUEST
        elif "new_post" in request.POST and context["is_owner"]:
            form = PublishForm(request.POST, request.FILES, initial={"author_id": context["author_id"]})
            if form.is_valid:
                # NEED FIX
                publication = form.save(commit=False)
                publication.content_type = ContentType.objects.get_for_model(request.user)
                publication.save()
                form.save()
                community.posts.add(publication)
                print("Yes")
                return redirect(f"/community/name-{context.get('name')}/")

        else:
            messages.error(request, "Something went wrong")

        return redirect(f"/community/name-{context.get('name')}/")

    def handle_follow_action(self, context):
        community = context.get("community_data")
        follower_obj, created = CommunityFollowers.objects.get_or_create(user=self.request.user, community=community)
        follower_obj.is_follow = not follower_obj.is_follow
        follower_obj.save()
        followers_count = CommunityFollowers.objects.filter(community=community, is_follow=True).count()
        return JsonResponse(
            {
                "followers_count": followers_count,
                "is_following": follower_obj.is_follow,
            }
        )

    def handle_send_request_action(self, context):
        community = context.get("community_data")
        request_obj, created = CommunityFollowRequests.objects.get_or_create(
            user=self.request.user, community=community
        )

        if not request_obj.send_status:
            follow_request_link = reverse("community_followers_requests", kwargs={"name": community.name})
            message = mark_safe(
                f"There is your new follow request: {request_obj.user.username}\n"
                f'Check your follow request list: <a href="{follow_request_link}">Request List</a>.'
            )
            Notification.objects.create(user=community.admins.get(is_owner=True).user, message=message)

            request_obj.send_status = True
        request_obj.save()

        return JsonResponse(
            {
                "request_status": request_obj.send_status,
            }
        )


class CreateCommunityView(View):
    template_name = "community/create_community.html"
    form_class = CreateCommunityForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            community = form.save(commit=True)
            moderators, created = Moderators.objects.get_or_create(user=request.user, is_owner=True)
            community.admins.add(moderators)
            return redirect(f"/community/name-{form.cleaned_data['name']}/")

        else:
            return render(request, self.template_name, {"form": form})


class CommunityListView(ListView):
    model = Community
    template_name = "community/community_list.html"


class CommunityFollowersListView(ListView):
    model = CommunityFollowers
    template_name = "community/community_detail/community_followers/community_followers.html"

    def get_queryset(self):
        followers = CommunityFollowers.objects.filter(
            community=get_object_or_404(Community, name=self.kwargs["name"]), is_follow=True
        ).all()
        return followers


class FollowersRequestListView(View):
    template_name = "community/community_detail/community_followers/follow_requests.html"

    def get_context_data(self, **kwargs):
        community = get_object_or_404(Community, name=self.kwargs["name"])
        followers = CommunityFollowRequests.objects.filter(community=community, accepted=False, send_status=True).all()
        return {"communityfollowers_list": followers}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            community = get_object_or_404(Community, name=self.kwargs["name"])
            user_id = request.POST.get("user")
            accept_obj = CommunityFollowRequests.objects.get(
                community=community, user=user_id, accepted=False, send_status=True
            )
            if request.POST.get("action") == "accept":
                accept_obj.delete()
                follow_r_obj, created = CommunityFollowers.objects.get_or_create(
                    user=accept_obj.user, community=community
                )
                follow_r_obj.is_follow = True
                follow_r_obj.save()
            elif request.POST.get("action") == "reject":
                accept_obj.delete()

        return JsonResponse({"success": "ok"})


class AdminPanelView(ViewWitsContext):
    template_name = "community/community_detail/admin_panel/adminpanel.html"
    """
    What needs to be added:
        1. Possibility of banning users
        2. Granting privileges (admin or moderator)
        3. Removal of privileges
        4. View recent activity
        5. Possibility to delete/hide posts
        
        and more
    """

    def get_context_data(self, request, **kwargs):
        context = super().get_context_data(request)
        instance = get_object_or_404(Community, name=self.kwargs["name"])

        # Community managers data
        context["owner"] = get_object_or_404(Moderators, is_owner=True)
        context["admins"] = Moderators.objects.filter(is_admin=True)
        context["moderators"] = Moderators.objects.filter(is_moderator=True)

        if not context["admins"]:
            context["admins"] = "You have no admins yet"
        if not context["moderators"]:
            context["moderators"] = "You have no moderators yet"

        # Community base data
        context["followers"] = CommunityFollowers.objects.filter(community=instance, is_follow=True).count()

        # Get community publications
        owner = instance.admins.filter(is_owner=True).first()
        if owner:
            context["all_posts"] = list(Publication.objects.filter(author_id=owner.user.id).values())
        else:
            context["all_posts"] = "You don't have any publication, but you can change that right now!"

        # context["last_actions"] = ...
        # context["black_list"] = ...

        context["instance"] = instance
        return context

    @method_decorator(owner_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)

        if "edit" in request.GET:
            edit_template = "community/create_community.html"
            form = CreateCommunityForm(instance=context["instance"])
            return render(request, edit_template, {"form": form})

        if "followers_list" in request.GET:
            return self.get_followers(request)

        if "put_ban" in request.GET:
            return self.ban_user

        return render(request, self.template_name, context)

    @method_decorator(owner_required)
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        form = CreateCommunityForm(request.POST, instance=context["instance"])
        edit_template = "community/create_community.html"
        redirect_url = f"/community/name-{self.kwargs['name']}/"

        redirect_response = base_post_method(form, redirect_url)
        if redirect_response:
            return redirect_response

        return render(request, edit_template, {"form": form})

    def get_followers(self, request, **kwargs):
        followers = CommunityFollowers.objects.filter(
            community=get_object_or_404(Community, name=self.kwargs["name"]), is_follow=True
        ).all()
        template = "community/community_detail/admin_panel/uses_list.html"
        return render(
            request, template, {"followers": followers, "instance": self.get_context_data(request)["instance"]}
        )

    def ban_user(self, request, *args, **kwargs):  # It's not over yet
        if request.method == "GET":
            ban_template = "community/community_detail/admin_panel/put_ban.html"
            community_id = Community.objects.get(name=self.kwargs["name"]).id
            follower_id = CommunityFollowers.objects.get(
                community=community_id, is_follow=True, id=self.kwargs["follower_id"]
            )
            form = BlackListForm(initial={"community": community_id, "user": follower_id})

            return render(request, ban_template, {"form": form})

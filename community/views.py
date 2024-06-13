from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import ListView

from app.models import Notification
from community.forms import CreateCommunityForm
from community.models import Community, CommunityFollowers, CommunityFollowRequests
from core import settings
from users.forms import PublishForm
from users.models import CustomUser, Moderators


class CommunityView(View):
    template_name = "community/community_detail/community_main_page.html"

    def get_context_data(self, **kwargs):
        name = self.kwargs.get("name")
        community_data = Community.objects.get(name=name)
        publication_form = PublishForm(
            initial={
                "author_id": community_data.admins.get(
                    is_owner=True,
                ).user
            }
        )
        community_followers = CommunityFollowers.objects.filter(community=community_data, is_follow=True).all()
        is_follow_user = CommunityFollowers.objects.filter(
            community=community_data, is_follow=True, user=self.request.user.id
        ).all()
        request_status = CommunityFollowRequests.objects.filter(
            community=community_data, user=self.request.user.id
        ).all()
        return {
            "publication_form": publication_form,
            "name": name,
            "community_data": community_data,
            "community_followers": community_followers,
            "is_follow_user": is_follow_user,
            "request_status": request_status,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["follow_value"] = "Unfollow" if context["is_follow_user"].exists() else "Follow"
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        action = self.request.POST.get("action")

        if action == "follow" or action == "unfollow":
            return self.handle_follow_action(context)
        elif action == "send_request":
            return self.handle_send_request_action(context)
        else:
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
        followers = CommunityFollowRequests.objects.filter(community=community).all()
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
            if request.POST.get("accept"):
                accept_obj.accepted = True
                CommunityFollowers.objects.create(user=accept_obj, community=community, is_follow=True)
            elif request.POST.get("reject"):
                accept_obj.accepted = False
            accept_obj.save()

        return JsonResponse({"success": "ok"})

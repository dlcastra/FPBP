from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView

from community.forms import CreateCommunityForm
from community.models import Community, CommunityFollowers
from core import settings
from users.forms import PublishForm
from users.models import CustomUser, Moderators


class CommunityView(View):
    template_name = "community/community_detail/community_main_page.html"

    def get_context_data(self, **kwargs):
        name = self.kwargs.get("name")
        user = CustomUser.objects.get(id=self.request.user.id)
        community_data = Community.objects.get(name=name)
        publication_form = PublishForm(initial={"author_id": user.id})
        community_followers = CommunityFollowers.objects.filter(community=community_data, is_follow=True).all()
        is_follow_user = CommunityFollowers.objects.filter(community=community_data, is_follow=True, user=user).all()
        return {
            "user": user,
            "publication_form": publication_form,
            "name": name,
            "community_data": community_data,
            "community_followers": community_followers,
            "is_follow_user": is_follow_user,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["follow_value"] = "Unfollow" if context["is_follow_user"].exists() else "Follow"
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        community = context.get("community_data")
        user = context.get("user")
        publication_form = PublishForm(request.POST, initial={"author_id": request.user})

        if publication_form.is_valid() and community.admins.filter(user=user.id, is_owner=True):
            publication = publication_form.save(commit=False)
            publication.author_id = request.user.id
            publication.content_type = ContentType.objects.get_for_model(Community)
            publication.save()
            community.posts.add(publication.id)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            follower_obj, created = CommunityFollowers.objects.get_or_create(user=request.user, community=community)
            follower_obj.is_follow = not follower_obj.is_follow
            follower_obj.accepted = not follower_obj.accepted
            if follower_obj.is_follow and follower_obj.accepted and not community.is_private:

                follower_obj.save()
                return JsonResponse(
                    {
                        "followers_count": CommunityFollowers.objects.filter(
                            community=community, is_follow=True
                        ).count(),
                        "is_following": follower_obj.is_follow,
                    }
                )
            elif not follower_obj.is_follow and community.is_private and not follower_obj.accepted:
                follower_obj.save()
                follow_request_link = self.request.build_absolute_uri(
                    f"/community/name-{community.name}/followers/requests/"
                )
                send_mail(
                    subject="Accept follower",
                    message=f"There is your new follow request: {follower_obj.user.username}\n Check your follow request list:{follow_request_link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[
                        community.admins.get(is_owner=True).user.email,
                    ],
                )

            return redirect(f"/community/name-{context.get('name')}/")


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
        followers = CommunityFollowers.objects.filter(community=community, is_follow=False, accepted=False).all()
        return {"communityfollowers_list": followers}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            user_id = request.POST.get("user")
            community = get_object_or_404(Community, name=self.kwargs["name"])
            updated = CommunityFollowers.objects.filter(user_id=user_id, community=community).update(
                accepted=True, is_follow=True
            )

            if updated:
                return JsonResponse({"success": "ok"})
            else:
                return JsonResponse({"error": "Something went wrong"}, status=400)
        return JsonResponse({"error": "Invalid request"}, status=400)

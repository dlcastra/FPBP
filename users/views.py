from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView

from app.mixins import CommentsHandlerMixin, RemoveCommentsMixin, DetailMixin
from .forms import CustomUserChangeForm, PublishForm
from .models import CustomUser, Followers, Publication


# ------------------------ Users Form ------------------------


class CustomUserChangeView(LoginRequiredMixin, View):
    form_class = CustomUserChangeForm
    template_name = "account/change_user_data.html"
    success_url = "/change-data/"

    def get(self, request):
        form = self.form_class(instance=request.user)
        connections = SocialAccount.objects.filter(user_id=request.user.id)
        connected_provider_ids = connections.values_list("provider", flat=True)
        return render(
            request,
            self.template_name,
            {"form": form, "connections": connections, "connected_provider_ids": connected_provider_ids},
        )

    def post(self, request):
        form = self.form_class(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        else:
            connections = SocialAccount.objects.filter(user_id=request.user.id)
            connected_provider_ids = connections.values_list("provider", flat=True)
            return render(
                request,
                self.template_name,
                {"form": form, "connections": connections, "connected_provider_ids": connected_provider_ids},
            )


# ------------------------ Disconnect Account func ------------------------
@login_required
def disconnect_account(request, provider):
    if request.method == "POST":
        try:
            account = SocialAccount.objects.get(user=request.user, provider=provider)
            account.delete()
            return JsonResponse({"success": True})
        except SocialAccount.DoesNotExist:
            return JsonResponse({"error": "Account not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method."}, status=400)


# ------------------------ USERS AND USER PROFILE VIEWS ------------------------
class AllUsers(ListView):
    model = CustomUser
    template_name = "account/all_users.html"


class UserPageView(LoginRequiredMixin, View):
    template_name = "account/user_page.html"

    def get_context_data(self, request, **kwargs):
        username = self.kwargs.get("username")
        user = CustomUser.objects.get(username=username)
        user.followers_count = Followers.objects.filter(user=user, is_follow=True).count()
        user.followings_count = Followers.objects.filter(following=user, is_follow=True).count()
        publications = Publication.objects.filter(
            author_id=user.id, content_type=ContentType.objects.get_for_model(CustomUser)
        )
        is_following = Followers.objects.filter(user=user, following=request.user, is_follow=True).exists()
        context = {
            "user": user,
            "followers_count": user.followers_count,
            "followings_count": user.followings_count,
            "publications": publications,
            "is_following": is_following,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            username = self.kwargs.get("username")
            user = CustomUser.objects.get(username=username)
            follows_obj, created = Followers.objects.get_or_create(user=user, following=request.user)
            follows_obj.is_follow = not follows_obj.is_follow
            follows_obj.save()

            user.followers_count = Followers.objects.filter(user=user, is_follow=True).count()
            is_following = follows_obj.is_follow

            return JsonResponse({"followers_count": user.followers_count, "is_following": is_following})
        else:
            context = self.get_context_data(request, **kwargs)
            return render(request, self.template_name, context)


# ------------------------ PUBLICATION VIEWS ------------------------


class CreatePublication(View):
    class_form = PublishForm
    template_name = "publications/create_publication.html"

    def get(self, request, *args, **kwargs):
        form = self.class_form(initial={"author_id": request.user.id})
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.class_form(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.author_id = request.user.id
            publication.content_type = ContentType.objects.get_for_model(request.user)
            publication.save()
            form.save()
            return redirect(f"/publication/{publication.id}/")
        else:
            return render(request, self.template_name, {"form": form})


class PublicationDetailView(DetailMixin, View):

    def get_model_class(self):
        return Publication

    def get_form_class(self):
        return PublishForm

    def get_context_data(self, request, **kwargs):
        context = super().get_context_data(request)
        get_user = CustomUser.objects.get(id=request.user.id)
        context["author"] = get_user.username

        return context

    def render_main_template(self):
        return "publications/publication_detail/publication_detail.html"

    def render_edit_template(self):
        return "publications/publication_detail/edit_publication.html"

    def get_redirect_url(self):
        return f"/publication/{self.kwargs['pk']}"

    def get_comments_template(self):
        return "publications/publication_detail/answers.html"


# ------------------------ COMMENTS SECTION ------------------------


class PublicationCommentsHandlerView(CommentsHandlerMixin, View):
    def get_model_class(self):
        return Publication

    def get_template(self):
        return "publications/publication_detail/answers.html"


class RemoveCommentPublication(RemoveCommentsMixin, View):
    def post(self, request, *args, **kwargs):
        return self.remove_comment(request, *args, **kwargs)

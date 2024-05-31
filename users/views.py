from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from .forms import CustomUserChangeForm, PublishForm
from .models import CustomUser, Followers, Publication


######## Users Form ########


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


# Disconnect Account func
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


class UserPageView(LoginRequiredMixin, View):
    template_name = "account/user_page.html"

    def get_context_data(self, request, **kwargs):
        username = self.kwargs.get("username")
        user = CustomUser.objects.get(username=username)
        user.followers_count = Followers.objects.filter(user_id=user.id, is_follow=True).count()
        user.followings_count = Followers.objects.filter(following_id=user.id, is_follow=True).count()
        publications = Publication.objects.filter(user_id=user.id).all()
        context = {
            "user": user,
            "publications": publications,
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return render(request, self.template_name, context)


######### Publications Form #########


class CreatePublication(View):
    class_form = PublishForm
    template_name = "publications/create_publication.html"

    def get(self, request, *args, **kwargs):
        form = self.class_form()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.class_form(request.POST)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.user = self.request.user
            publication.save()
            return redirect(f"/user-page/{publication.user.username}/{publication.slug}/")
        else:
            return render(request, self.template_name, {"form": form})


class PublicationDetailView(View):
    template_name = "publications/publication_detail/publication_detail.html"

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug")
        publication_data = Publication.objects.get(slug=slug)
        return render(request, self.template_name, {"publication_data": publication_data})

    # def post(self, request, *args, **kwargs):
    #

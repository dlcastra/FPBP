import json

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from core.mixins import RemoveCommentsMixin, DetailMixin
from .forms import CustomUserChangeForm, PublishForm
from .models import CustomUser, Followers, Publication, Chat, ChatBlackList


# ------------------------ Users Form ------------------------


class CustomUserChangeView(LoginRequiredMixin, View):
    form_class = CustomUserChangeForm
    template_name = "account/change_user_data.html"
    success_url = "/change-data/"

    def get(self, request):
        """
        Displays a page for editing user data

        :param request: GET request
        :return: Render template with dictionary context data:
            - form (form_class): CustomUserChangeForm instance
            - connections (list): List of user connection social accounts
            - connected_provider_ids (list[int]): List of provider ids
        """
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


class FollowersListView(ListView):
    template_name = "account/followers_list.html"

    def get_queryset(self):
        return Followers.objects.filter(user__username=self.kwargs["username"], is_follow=True)


class FollowingsListView(ListView):
    template_name = "account/followings_list.html"

    def get_queryset(self):
        return Followers.objects.filter(following__username=self.kwargs["username"], is_follow=True)


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
        """
        :return: Dictionary context data:
            - user (instance)
            - followers_count (int)
            - followings_count (int)
            - publication (list): List of user publications
            - is_following (list): List of user followings
        """
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
        if request.GET.get("create_chat"):
            recipient = CustomUser.objects.get(username=self.kwargs.get("username"))
            try:
                Chat.objects.get(
                    Q(sender_id=request.user.id, recipient_id=recipient.id)
                    | Q(sender_id=recipient.id, recipient_id=request.user.id)
                )
            except Chat.DoesNotExist:
                Chat.objects.create(sender_id=request.user.id, recipient_id=recipient.id)
            return redirect("chat/")
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Responsible for handling the user subscription system

        :param request: HTTP request object that can include 'XMLHttpRequest' from headers
        :param args: Additional arguments
        :param kwargs: Get 'username' from URL path

        :return: JsonResponse or Render template with context:
            - If following end with success: Return JsonResponse with followers_count (int) and is_following (bool)
            - For else: Render template with context
        """
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
        return "main_page/answers.html"


# ------------------------ COMMENTS SECTION ------------------------


class RemoveCommentPublication(RemoveCommentsMixin, View):
    def post(self, request, *args, **kwargs):
        return self.remove_comment(request, *args, **kwargs)


# ------------------------ Chat Section ---------------------------


class ConversationView(View):
    model = Chat
    template_name = "conversations/chat.html"

    def get_context_data(self, request, **kwargs):
        recipient = self.kwargs.get("username")
        sender = request.user.username
        chat = self.model.objects.get(
            Q(sender__username=request.user.username, recipient__username=recipient)
            | Q(sender__username=recipient, recipient__username=request.user.username)
        )
        messages = chat.message.filter().all()
        context = {
            "recipient": recipient,
            "sender": sender,
            "chat": chat,
            "messages": messages,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        chat = context.get("chat")
        if "settings" in request.GET:
            return redirect("settings/")
        if chat:
            black_list = ChatBlackList.objects.filter(user=request.user, chat_id=chat.id)
            if black_list:
                context["not_allowed"] = True
            return render(request, self.template_name, context=context)
        else:
            return HttpResponse(
                "Chat not found",
                status=404,
            )


class ChatList(ListView):
    model = Chat
    template_name = "conversations/chat_list.html"

    def get_queryset(self):
        return Chat.objects.filter(Q(sender=self.request.user) | Q(recipient=self.request.user))


class ChatSettings(View):
    model = Chat
    template_name = "conversations/chat_settings.html"

    def get_context_data(self, **kwargs):
        username = self.kwargs.get("username")
        user = CustomUser.objects.get(username=username)
        chat = self.model.objects.get(Q(recipient=user) | Q(sender=user))
        return {"chat": chat, "user": user}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        chat = context.get("chat")
        user = context.get("user")
        is_blocked = ChatBlackList.objects.filter(chat=chat, user=user).exists()
        block_btn_value = "Unblock user" if is_blocked else "Block user"
        context["block_btn_value"] = block_btn_value
        return render(request, self.template_name, context)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        chat = context.get("chat")
        user = context.get("user")
        data = json.loads(request.body.decode("utf-8"))

        action = data.get("action")
        if action == "block_user":
            bl_list, created = ChatBlackList.objects.get_or_create(user=user, chat_id=chat.id)
            bl_list.save()
            context["block_btn_value"] = "Unblock user"
            response = {"status": "success", "action": "blocked"}
        elif action == "unblock_user":
            bl_list = ChatBlackList.objects.filter(user=user, chat_id=chat.id).first()
            if bl_list:
                bl_list.delete()
                context["block_btn_value"] = "Block user"
                response = {"status": "success", "action": "unblocked"}
            else:
                response = {"status": "error", "message": "Not found"}
        else:
            response = {"status": "error", "message": "Invalid action"}

        return JsonResponse(response)

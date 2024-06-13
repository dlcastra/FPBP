import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView

from users.models import CustomUser, Publication, Followers
from .constants import PROGRAMMING_LANGUAGES
from .forms import ThreadForm
from .helpers import post_request_details
from .mixins import CommentsHandlerMixin, RemoveCommentsMixin, DetailMixin
from .models import ProgrammingLanguage, TutorialPage, SubSection, Notification
from .models import Thread


# ------------------------ BASED VIEWS ------------------------
class MainPageView(View):
    template_name = "main_page/index.html"

    @staticmethod
    def get_context_data(request):
        # user = get_object_or_404(CustomUser, username=request.user.username)
        notifications = Notification.objects.filter(user=request.user).order_by("id")
        context = {"prog_lang": PROGRAMMING_LANGUAGES, "notifications": notifications}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            data = json.loads(request.body)
            if "mark_read" in data:
                notification = Notification.objects.get(user=request.user, id=data["id"])
                notification.delete()
                return HttpResponse(json.dumps({"status": "ok"}), content_type="application/json")

        return HttpResponse(json.dumps({"status": "error"}), status=400, content_type="application/json")


# ------------------------ THREADS VIEWS ------------------------
class TutorialPageView(View):
    template_name = "tutorials/index.html"

    def get(self, request, slug, page_id, *args, **kwargs):
        language = get_object_or_404(ProgrammingLanguage, slug=slug)
        page = get_object_or_404(TutorialPage, language=language, id=page_id)
        subsections = SubSection.objects.filter(page=page)
        context = {
            "language": language,
            "page": page,
            "subsections": subsections,
        }
        return render(request, self.template_name, context)


class ThreadsPageView(View):
    template_name = "threads/all_threads/threads_page.html"

    @staticmethod
    def get_context_data(request):
        search_query = request.GET.get("search", "")
        if search_query:
            threads = Thread.objects.filter(title__contains=search_query).order_by("id")
        else:
            threads = Thread.objects.order_by("-id")
        context = {"threads": threads, "search_query": search_query}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        if "create" in request.GET:
            return redirect("new_thread")

        return render(request, self.template_name, context)


class CreateThreadView(View):
    template_name = "threads/create_thread.html"
    form_class = ThreadForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial={"author": request.user})
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        redirect_response = post_request_details(request, form, "/threads/")

        if redirect_response:
            return redirect_response

        return render(request, self.template_name, {"form": form})


class ThreadDetailView(DetailMixin, DetailView):
    def get_model_class(self):
        return Thread

    def get_form_class(self):
        return ThreadForm

    def render_main_template(self):
        return "threads/threads_detail/thread_detail.html"

    def render_edit_template(self):
        return "threads/threads_detail/edit_thread.html"

    def get_redirect_url(self):
        return f"/thread-detail/{self.kwargs['pk']}"

    def get_comments_template(self):
        return "threads/threads_detail/answers.html"


class ThreadCommentsHandlerView(CommentsHandlerMixin, View):

    def get_model_class(self):
        return Thread

    def get_template(self):
        return "threads/threads_detail/answers.html"


class RemoveCommentThread(RemoveCommentsMixin, View):
    def post(self, request, *args, **kwargs):
        return self.remove_comment(request, *args, **kwargs)


# ------------------------ RECOMMENDATION FEED ------------------------
class RecommendationFeedView(View):
    template_name = "recommendations/index.html"

    def get_context_data(self, request, **kwargs):
        context = {}
        # DATA FROM USER FRIENDS
        user = CustomUser.objects.get(username=request.user.username)
        following_user_list_id = Followers.objects.filter(following=user, is_follow=True).values_list(
            "user_id", flat=True
        )
        content_from_follow = Publication.objects.filter(author_id__in=following_user_list_id).order_by("-published_at")

        # DATA FROM SUBSCRIBED COMMUNITIES
        # ...

        # DATA FROM BASE COMMUNITIES
        # ...

        # DATA FROM THREADS
        # ...

        # ADVERTISING POSTS
        # ...

        # RECOMMENDED POSTS(posts from communities to which the user is not subscribed)
        # ...

        # CONTEXT SECTION
        context["content_from_follow"] = content_from_follow

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

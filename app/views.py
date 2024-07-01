import json

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView

from community.models import Community
from users.models import CustomUser, Publication, Followers
from .constants import PROGRAMMING_LANGUAGES
from .forms import ThreadForm
from core.helpers import post_request_details, data_handler
from core.mixins import RemoveCommentsMixin, DetailMixin
from .models import ProgrammingLanguage, TutorialPage, SubSection, Notification, Comments
from .models import Thread


# ------------------------ BASED VIEWS ------------------------
class MainPageView(View):
    template_name = "main_page/index.html"

    @staticmethod
    def get_context_data(request):
        if request.user.is_authenticated:
            notifications = Notification.objects.filter(user=request.user).order_by("id")
            publication_content_type = ContentType.objects.get_for_model(Publication)
            publications_obj = [
                {
                    "title": publication.title,
                    "photo": publication.attached_file if publication.attached_file is not None else "",
                    "link": f"/publication/{publication.id}/",
                    "id": publication.id,
                    "content_type": publication_content_type,
                    "comments": Comments.objects.filter(
                        object_id=publication.id, content_type=publication_content_type
                    ),
                }
                for publication in Publication.objects.filter().all()
            ]
            thread_content_type = ContentType.objects.get_for_model(Thread)
            threads_obj = [
                {
                    "title": thread.title,
                    "photo": thread.image if thread.image is not None else "",
                    "link": f"thread-detail/{thread.pk}",
                    "id": thread.id,
                    "content_type": thread_content_type,
                    "comments": Comments.objects.filter(object_id=thread.id, content_type=thread_content_type),
                }
                for thread in Thread.objects.filter().all()
            ]
            print(threads_obj)

            contents = publications_obj + threads_obj
            context = {"prog_lang": PROGRAMMING_LANGUAGES, "notifications": notifications, "contents": contents}
            return context
        else:
            context = {"prog_lang": PROGRAMMING_LANGUAGES}
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
            if "mark_read_all" in data:
                notification = Notification.objects.filter(user=request.user).all()
                notification.delete()
                return HttpResponse(json.dumps({"status": "ok"}), content_type="application/json")
        return HttpResponse(json.dumps({"status": "error"}), status=400, content_type="application/json")


class SearchView(View):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get("search", "")
        if search_query:
            users = CustomUser.objects.filter(username__icontains=search_query).all()
            threads = Thread.objects.filter(title__icontains=search_query).all()
            communities = Community.objects.filter(name__icontains=search_query).all()

            res_user = [{"title": user.username, "link": f"/user-page/{user.username}/"} for user in users]
            res_threads = [{"title": thread.title, "link": f"/thread-detail/{thread.id}"} for thread in threads]
            res_communities = [
                {"title": community.name, "link": f"/community/name-{community.name}/"} for community in communities
            ]

            results = res_user + res_threads + res_communities
            return render(request, "main_page/search_list.html", {"results": results})
        return render(request, "main_page/search_bar.html")


class AutocompleteSearchView(DetailView):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("term", "")
        users = CustomUser.objects.filter(username__icontains=query)
        threads = Thread.objects.filter(title__icontains=query)
        communities = Community.objects.filter(name__icontains=query)

        # Collecting data for autocomplete suggestions
        suggestions = []

        for user in users:
            suggestions.append({"label": user.username, "url": f"/user-page/{user.username}/"})

        for thread in threads:
            suggestions.append({"label": thread.title, "url": f"/thread-detail/{thread.id}"})

        for community in communities:
            suggestions.append({"label": community.name, "url": f"/community/name-{community.name}/"})

        return JsonResponse(suggestions, safe=False)


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
        return "main_page/answers.html"


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

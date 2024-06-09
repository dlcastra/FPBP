from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView

from users.forms import PublishForm
from users.models import CustomUser, Moderators, Publication
from .constants import PROGRAMMING_LANGUAGES
from .forms import ThreadForm, CommunityForm, CreateCommunityForm
from .helpers import post_request_details
from .mixins import CommentsHandlerMixin, RemoveCommentsMixin, DetailMixin
from .models import ProgrammingLanguage, TutorialPage, SubSection, Community
from .models import Thread


class MainPageView(View):
    template_name = "main_page/index.html"

    @staticmethod
    def get_context_data(request):
        user = get_object_or_404(CustomUser, username=request.user.username)
        context = {"prog_lang": PROGRAMMING_LANGUAGES, "user": user}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)


# THREADS VIEWS
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


class CommunityView(View):
    template_name = "community/community_detail/community_main_page.html"

    def get_context_data(self, **kwargs):
        name = self.kwargs.get("name")
        user = CustomUser.objects.get(username=self.request.user.username)
        community_data = Community.objects.get(name=name)
        follower_count = community_data.followers.count()
        publication_form = PublishForm(initial={"author_id": community_data.id})
        return {
            "user": user,
            "publication_form": publication_form,
            "name": name,
            "follower_count": follower_count,
            "community_data": community_data,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        community = context.get("community_data")
        publication_form = PublishForm(request.POST, initial={"object_id": request.user})

        if publication_form.is_valid():
            publication = publication_form.save(commit=False)
            publication.author_id = request.user.id
            publication.content_type = ContentType.objects.get_for_model(Community)
            publication.save()
            community.posts.add(publication.id)
        else:
            messages.error(request, "Invalid data")

        return redirect(f"/community/{context.get('name')}/")


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
            return redirect(f"/community/{form.cleaned_data['name']}/")
        else:
            return render(request, self.template_name, {"form": form})

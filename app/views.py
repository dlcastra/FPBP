from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView, DetailView

from users.models import CustomUser
from .constants import PROGRAMMING_LANGUAGES
from .forms import ThreadForm
from .helpers import data_handler, post_request_threads
from .models import ProgrammingLanguage, TutorialPage, SubSection
from .models import Thread, ThreadAnswer


# TEMPLATE VIEWS
class PythonFirstPageView(TemplateView):
    template_name = "tutorials/python/python_main.html"

    def get(self, request, *args, **kwargs):
        if "next" in request.GET:
            return redirect("/tutorials/mainpy/1/")

        return render(request, self.template_name)


# NORMAL VIEWS
class MainPageView(View):
    template_name = "main_page/index.html"

    @staticmethod
    def get_context_data(request):
        context = {"prog_lang": PROGRAMMING_LANGUAGES}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)


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
        threads = Thread.objects.order_by("-id")
        context = {"threads": threads}

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
        redirect_response = post_request_threads(request, form, "/threads/")

        if redirect_response:
            return redirect_response

        return render(request, self.template_name, {"form": form})


class ThreadDetailView(DetailView):
    model = Thread
    form_class = ThreadForm
    template_name = "threads/threads_detail/thread_detail.html"

    def get_context_data(self, request, **kwargs):
        user = request.user
        thread_pk = self.kwargs.get("pk")
        thread = Thread.objects.filter(id=thread_pk).all()
        thread_detail = get_object_or_404(Thread, pk=thread_pk)
        answer = ThreadAnswer.objects.filter(thread_id=thread_pk).all()

        get_context = data_handler(self.request, thread_pk)
        get_context["thread_detail"] = thread_detail
        context = {
            "user": user,
            "thread": thread,
            "thread_detail": thread_detail,
            "answer": answer,
            "get_context": get_context,
        }

        return context

    def get_object(self, queryset=None):
        thread_pk = self.kwargs.get("pk")
        return get_object_or_404(Thread, pk=thread_pk)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        template = self.template_name

        if "edit" in request.GET:
            edit_template = "threads/threads_detail/edit_thread.html"
            form = self.form_class(instance=self.get_object())
            return render(request, edit_template, {"form": form})

        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=self.get_object())
        thread_pk = kwargs["pk"]
        redirect_response = post_request_threads(request, form, f"/thread-detail/{thread_pk}")

        if redirect_response:
            return redirect_response

        context = self.get_context_data(request, **kwargs)
        context["form"] = form
        return render(request, self.template_name, context)


class AnswerHandler(View):

    def get_context_data(self, request, **kwargs):
        pk = self.kwargs.get("pk")
        get_data = data_handler(request, pk)
        user_id = get_data["user_id"]
        thread = get_object_or_404(Thread, pk=pk)

        context = {"user_id": user_id, "thread": thread, "pk": pk}
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        thread = context["thread"]

        if thread:
            content = request.POST.get("feedback")
            user = CustomUser.objects.get(id=context["user_id"])
            ThreadAnswer.objects.create(user=user, title=thread.title, context=content, thread=thread)
            return JsonResponse(data_handler(request, context["pk"]))

        return JsonResponse({"message": "Invalid request"}, status=400)


class RemoveAnswer(View):
    def post(self, request, *args, **kwargs):
        answer_id = self.kwargs.get("answer_id")
        try:
            answer = ThreadAnswer.objects.get(id=answer_id)
            answer.delete()

        except ThreadAnswer.DoesNotExist:
            return JsonResponse({"error": "Answer does not exist"}, status=404)
        return HttpResponse(status=204)

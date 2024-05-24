from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, DetailView

from .constants import PROGRAMMING_LANGUAGES
from .forms import ThreadForm
from .models import Thread


# TEMPLATE VIEWS
class PythonFirstPageView(TemplateView):
    template_name = "tutorials/python/python_main.html"


# NORMAL VIEWS
class MainPageView(View):
    template_name = "main_page/index.html"

    @staticmethod
    def get_context_data(request):
        context = {"prog_lang": PROGRAMMING_LANGUAGES}
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class ThreadsPageView(View):
    template_name = "threads/all_threads/threads_page.html"

    def get_context_data(self, request):
        threads = Thread.objects.all()
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
        print(request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        print(request.user)
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            if "image" in request.FILES:
                instance = request.FILES["image"]
            elif "file" in request.FILES:
                instance = request.FILES["file"]
            instance.author = request.user

            instance.save()
            form.save()
            return redirect("threads")

        return render(request, self.template_name, {"form": form})


class ThreadDetailView(DetailView):
    model = Thread
    form_class = ThreadForm
    template_name = "threads/threads_detail/thread_detail.html"

    def get_context_data(self, request, **kwargs):
        thread_pk = self.kwargs.get("pk")
        thread_detail = get_object_or_404(Thread, pk=thread_pk)
        thread = Thread.objects.filter(id=thread_pk)
        user = request.user
        context = {"thread_detail": thread_detail, "thread": thread, "user": user}

        return context

    def get_object(self, queryset=None):
        thread_pk = self.kwargs.get("pk")
        return get_object_or_404(Thread, pk=thread_pk)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        template = self.template_name

        if "edit" in request.GET:
            template = "threads/threads_detail/edit_thread.html"
            form = self.form_class(instance=self.get_object())
            return render(request, template, {"form": form})

        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=self.get_object())
        if form.is_valid():
            instance = form.save(commit=False)
            if "image" in request.FILES:
                instance = request.FILES["image"]
            elif "file" in request.FILES:
                instance = request.FILES["file"]
            instance.author = request.user

            instance.save()
            form.save()
            return redirect("detail", pk=instance.pk)

        context = self.get_context_data(request, **kwargs)
        context["form"] = form
        return render(request, self.template_name, context)

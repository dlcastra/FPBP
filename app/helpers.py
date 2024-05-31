from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.template.loader import render_to_string

from .models import Comments


def data_handler(request, pk):
    answer = Comments.objects.filter(object_id=pk).all()
    user = request.user
    user_id = user.id
    feedback_html = render_to_string(
        "threads/threads_detail/answers.html", {"answer": answer, "csrf_token": get_token(request), "user": user}
    )
    return {"feedback_html": feedback_html, "user_id": user_id, "csrf_token": get_token(request)}


def post_request_threads(request, form_with_files, redirect_url):
    form = form_with_files
    if form.is_valid():
        instance = form.save(commit=False)
        if "image" in request.FILES:
            instance.image = request.FILES["image"]
        elif "file" in request.FILES:
            instance.file = request.FILES["file"]
        instance.author = request.user
        instance.save()
        form.save()

        return HttpResponseRedirect(redirect_url)

from django.middleware.csrf import get_token
from django.template.loader import render_to_string

from .models import ThreadAnswer


def data_handler(request, pk):
    answer = ThreadAnswer.objects.filter(thread_id=pk).all()
    user = request.user
    user_id = user.id
    feedback_html = render_to_string(
        "threads/threads_detail/answers.html", {"answer": answer, "csrf_token": get_token(request), "user": user}
    )
    return {"feedback_html": feedback_html, "user_id": user_id, "csrf_token": get_token(request)}

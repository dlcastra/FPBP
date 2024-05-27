from django.urls import path

from app import views

urlpatterns = [
    path("", views.MainPageView.as_view(), name="index"),
    # URLS FOR THREADS
    path("threads/", views.ThreadsPageView.as_view(), name="threads"),
    path("new-thread/", views.CreateThreadView.as_view(), name="new_thread"),
    path("thread-detail/<int:pk>", views.ThreadDetailView.as_view(), name="detail"),
    path("post-feedback/<int:pk>", views.answer_handler, name="post_feedback"),
    path("remove-feedback/<int:answer_id>/", views.remove_answer, name="remove_answer"),
    # URLS FOR PROG LANGUAGES
    path("python/", views.PythonFirstPageView.as_view(), name="python_main"),
    path("tutorials/<str:slug>", views.TutorialPageView.as_view(), name="tutorials"),
]

from django.urls import path

from app import views

urlpatterns = [
    path("", views.MainPageView.as_view(), name="index"),
    path("threads/", views.ThreadsPageView.as_view(), name="threads"),
    path("new-thread/", views.CreateThreadView.as_view(), name="new_thread"),
    path("thread-detail/<int:pk>", views.ThreadDetailView.as_view(), name="detail"),
]

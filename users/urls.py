from django.urls import path

from users import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
]

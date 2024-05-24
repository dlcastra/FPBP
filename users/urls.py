from django.urls import path
from allauth.socialaccount.providers.google import urls
from users import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("activate/<user_signed>/", views.activate, name="activate")
]


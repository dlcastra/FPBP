from django.urls import path
from users import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("activate/<user_signed>/", views.activate, name="activate"),
    path("register/end_registration/", views.CustomAllAuthAccountCreationView.as_view(), name="end_registration"),
    path("logout/", views.logout_view, name="logout"),
]

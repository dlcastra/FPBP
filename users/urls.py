from django.urls import path, include, re_path
from users import views
from allauth.socialaccount.views import SignupView as SocialSignupView
from allauth.socialaccount.providers.google.urls import urlpatterns as google_urlpatterns
from allauth.account import views as account_views

urlpatterns = [
    path("change-data/", views.CustomUserChangeView.as_view(), name="change_data"),
    path("signup/", account_views.SignupView.as_view(), name="account_signup"),
    path("login/", account_views.LoginView.as_view(), name="account_login"),
    path("logout/", account_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", account_views.PasswordResetView.as_view(), name="account_reset_password"),
    re_path(
        r"^password-reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        account_views.PasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key",
    ),
    path(
        "password-reset/key/done/",
        account_views.PasswordResetFromKeyDoneView.as_view(),
        name="account_reset_password_from_key_done",
    ),
    path("password-reset/done/", account_views.PasswordResetDoneView.as_view(), name="account_reset_password_done"),
    path("change-password/", account_views.PasswordChangeView.as_view(), name="account_change_password"),
    path("set-password/", account_views.PasswordSetView.as_view(), name="account_set_password"),
    path(
        "accounts/github/login/callback/", include("allauth.socialaccount.providers.github.urls"), name="github_login"
    ),
    path("end-login3p/", SocialSignupView.as_view(), name="socialaccount_signup"),
    path("confirm-email/<key>/", account_views.ConfirmEmailView.as_view(), name="account_confirm_email"),
]
urlpatterns += google_urlpatterns

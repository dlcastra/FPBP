from django.urls import path, include, re_path
from users import views
from allauth.socialaccount import views as socialaccount_views
from allauth.socialaccount.views import ConnectionsView as SocialConnectionsView
from allauth.socialaccount import urls as socialaccount_urls
from allauth.account import views as account_views

urlpatterns = [
    path("change-data/", views.CustomUserChangeView.as_view(), name="socialaccount_connections"),
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
    path("accounts/", include("allauth.socialaccount.providers.google.urls"), name="google_login"),
    path("end-login3p/", socialaccount_views.SignupView.as_view(), name="socialaccount_signup"),
    path("confirm-email/<key>/", account_views.ConfirmEmailView.as_view(), name="account_confirm_email"),
    # path("change-data/connections/", socialaccount_views.ConnectionsView.as_view(), name="socialaccount_connections"),
    path("change-data/disconnect/<provider>/", views.disconnect_account, name="disconnect_account"),
    # path("change-data/connect/<provider>/", views.connect_account, name="connect_account"),
]

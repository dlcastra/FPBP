from django.urls import path
from users import views

urlpatterns = [
    path("change_data/", views.CustomUserChangeView.as_view(), name="change_data"),
]

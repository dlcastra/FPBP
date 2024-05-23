from celery import shared_task
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.core.signing import Signer, BadSignature
from django.views import View

from core.settings import EMAIL_HOST_USER
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect

from .models import CustomUser


# Activation mail sender
@shared_task
def send_activation_email(request, user_id):
    user_signed = Signer().sign(user_id)
    signed_url = request.build_absolute_uri(f"/activate/{user_signed}")
    send_mail(
        subject="Registration complete",
        message=("Click here to activate your account: " + signed_url),
        from_email=EMAIL_HOST_USER,
        recipient_list=[CustomUser.objects.get(pk=user_id).email],
        fail_silently=False,
    )
    return "sent activation email"


# Activate account function
def activate(request, user_signed):
    try:
        user_id = Signer().unsign(user_signed)
    except BadSignature:
        return redirect("/login/")
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return redirect("/login/")
    user.is_active = True
    user.save()
    return redirect("/login/")


# ===== User Creation/Logining =====
class RegisterView(View):
    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = "/"

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.instance.is_active = False
            form.save()
            send_activation_email(self.request, form.instance.id)
            return redirect(self.success_url)
        else:
            return render(request, self.template_name, {"form": form})


class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        user_login = CustomUser.objects.filter(username=user.username)
        if user_login.exists():
            return "/"
        else:
            return "/login/"


# ==================================

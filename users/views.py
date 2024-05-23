from django.contrib.auth.views import LoginView
from django.views import View
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect

from .models import CustomUser


class RegisterView(View):
    form_class = CustomUserCreationForm
    template_name = "register.html"
    success_url = "/"

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
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

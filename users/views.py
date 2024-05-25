from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from .forms import CustomUserChangeForm


class CustomUserChangeView(LoginRequiredMixin, View):
    form_class = CustomUserChangeForm
    template_name = "registration/change_user_data.html"
    success_url = "/change_data/"

    def get(self, request):
        form = self.form_class(instance=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        else:
            return render(request, self.template_name, {"form": form})

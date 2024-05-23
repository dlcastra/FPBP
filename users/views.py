from django.views import View
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect


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
            form.save()
            return redirect(self.success_url)
        else:
            return render(request, self.template_name, {"form": form})

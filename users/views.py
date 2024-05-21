from django.http import HttpResponse
from .forms import CustomUserCreationForm
from django.shortcuts import render


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("OK")
    return render(request, "register.html", {"form": CustomUserCreationForm()})

from django import forms
from django.http import HttpResponseRedirect


def post_request_details(request, form_with_files, redirect_url):
    form = form_with_files
    if form.is_valid():
        instance = form.save(commit=False)
        if "image" in request.FILES:
            instance.image = request.FILES["image"]
        elif "file" in request.FILES:
            instance.file = request.FILES["file"]
        instance.author = request.user
        instance.save()
        form.save()

        return HttpResponseRedirect(redirect_url)


def base_post_method(model_form, redirect_url):
    if model_form.is_valid():
        instance = model_form.save(commit=False)
        instance.save()
        model_form.save()
        return HttpResponseRedirect(redirect_url)


def form_check_len(context: str, min_len: int, max_len: int, min_error: str, max_error: str):
    if len(context) == 0:
        raise forms.ValidationError("Context cannot be empty")

    if len(context) < min_len:
        raise forms.ValidationError(f"{min_error}, minimum length is {min_len}")
    elif len(context) > max_len:
        raise forms.ValidationError(f"{max_error}, maximum length is {max_len}")

    return context

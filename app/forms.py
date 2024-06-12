import re

from django import forms
from .models import Thread
from .constants import FILE_MAX_SIZE


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ["title", "context", "author", "image", "file"]
        labels = {
            "title": "Thread headline",
            "context": "Description",
            "image": "Upload image(Optionally), Max size 2mb",
            "file": "Upload file(Optionally), Max size 2mb",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "The title should not be empty and exceed 255 characters."}),
            "context": forms.Textarea(
                attrs={"placeholder": "Describe your problem in detail, don't be shy. Minimum 50 characters."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super(ThreadForm, self).__init__(*args, **kwargs)
        self.fields["author"].widget = forms.HiddenInput()
        self.fields["author"].initial = kwargs.get("initial", {}).get("author")

    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) > 255:
            raise forms.ValidationError("Title is too long")
        elif len(title) == 0:
            raise forms.ValidationError("Title cannot be empty")

        return title

    def clean_context(self):
        context = self.cleaned_data["context"]
        if len(context) == 0:
            raise forms.ValidationError("Context cannot be empty")
        elif len(context) < 50:
            raise forms.ValidationError("Please add more details to the contex")

        if re.fullmatch(r"\d+", context):
            raise forms.ValidationError("Context cannot consist only of digits")

        return context

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image:
            if image.size > FILE_MAX_SIZE:
                raise forms.ValidationError("The image size must be less than 2 megabytes")

        return image

    def clean_file(self):
        file = self.cleaned_data["file"]
        if file:
            if file.size > FILE_MAX_SIZE:
                raise forms.ValidationError("The file size must be less than 2 megabytes")

        return file

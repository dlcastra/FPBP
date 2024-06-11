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
            "image": "Upload image(Optionally)",
            "file": "Upload file(Optionally)",
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
        # elif all(chr(context.isdigit())):
        #     raise forms.ValidationError("Context cannot consist only of numbers")

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

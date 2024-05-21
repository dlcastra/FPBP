from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    birthday = forms.DateField(required=True, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
                               input_formats=["%Y-%m-%d"])

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "first_name", "photo", "last_name", "birthday", "gender", "phone_number", "email")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("confirm_password")
        if password != password_confirmation:
            raise forms.ValidationError("Passwords must match.")
        return cleaned_data

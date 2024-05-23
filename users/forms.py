from django import forms
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Username"}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "First Name"}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Last Name"}))
    birthday = forms.DateField(
        required=True,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))
    phone_number = PhoneNumberField(
        required=True,
        widget=PhoneNumberPrefixWidget(),
    )
    password1 = forms.CharField(
        required=True, widget=forms.PasswordInput(attrs={"placeholder": "Password"}), label="Password"
    )
    password2 = forms.CharField(
        required=True, widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}), label="Confirm Password"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "photo",
            "birthday",
            "gender",
            "phone_number",
            "email",
            "password1",
            "password2",
        )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password1")
        password_confirmation = cleaned_data.get("password2")
        if password and password_confirmation and password != password_confirmation:
            self.add_error("password2", "Passwords must match.")
        return cleaned_data

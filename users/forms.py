from allauth.account.forms import SignupForm, ChangePasswordForm
from django import forms
from django.contrib.auth.forms import UserChangeForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from users.models import CustomUser


class CustomUserCreationForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields["username"] = forms.CharField(
            required=True, widget=forms.TextInput(attrs={"placeholder": "Username"})
        )
        self.fields["first_name"] = forms.CharField(
            required=False, widget=forms.TextInput(attrs={"placeholder": "First Name"})
        )
        self.fields["last_name"] = forms.CharField(
            required=False, widget=forms.TextInput(attrs={"placeholder": "Last Name"})
        )
        self.fields["photo"] = forms.ImageField(required=False)
        self.fields["birthday"] = forms.DateField(
            required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        )
        self.fields["email"] = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))
        self.fields["phone_number"] = PhoneNumberField(required=False, widget=PhoneNumberPrefixWidget())
        self.fields["password1"] = forms.CharField(
            required=True, widget=forms.PasswordInput(attrs={"placeholder": "Password"}), label="Password"
        )
        self.fields["password2"] = forms.CharField(
            required=True,
            widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
            label="Confirm Password",
        )

    def save(self, request):
        user = super(CustomUserCreationForm, self).save(request)
        user.username = self.cleaned_data["username"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.password1 = self.cleaned_data["password1"]
        user.password2 = self.cleaned_data["password2"]
        user.birthday = self.cleaned_data["birthday"]
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.photo = self.cleaned_data["photo"]
        user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Username"}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "First Name"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Last Name"}))
    birthday = forms.DateField(required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))
    phone_number = PhoneNumberField(required=False, widget=PhoneNumberPrefixWidget())
    photo = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "photo",
            "birthday",
            "phone_number",
            "email",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password", None)


class CustomPasswordChangeForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields["oldpassword"] = forms.CharField(required=True, widget=forms.PasswordInput(), label="Old Password")
        self.fields["password1"] = forms.CharField(required=True, widget=forms.PasswordInput(), label="New Password")
        self.fields["password2"] = forms.CharField(
            required=True, widget=forms.PasswordInput(), label="Confirm New Password"
        )

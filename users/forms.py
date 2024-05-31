from allauth.account.forms import SignupForm, ChangePasswordForm, SetPasswordForm, ResetPasswordKeyForm
from allauth.socialaccount.forms import SignupForm as SocialAccountSignUpForm
from django import forms
from django.contrib.auth.forms import UserChangeForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from users.models import CustomUser, Publication


class CustomUserCreationForm(forms.ModelForm):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Username"}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "First Name"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Last Name"}))
    photo = forms.ImageField(required=False)
    birthday = forms.DateField(required=True, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))
    phone_number = PhoneNumberField(required=False, widget=PhoneNumberPrefixWidget())
    password1 = forms.CharField(
        required=True, widget=forms.PasswordInput(attrs={"placeholder": "Password"}), label="Password"
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
        label="Confirm Password",
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "photo",
            "birthday",
            "password1",
            "password2",
        )


class CustomAccountCreationForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(CustomAccountCreationForm, self).__init__(*args, **kwargs)
        custom_form = CustomUserCreationForm()
        self.fields.update(custom_form.fields)

    def save(self, request):
        user = super(CustomAccountCreationForm, self).save(request)
        user.username = self.cleaned_data["username"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.photo = self.cleaned_data["photo"]
        user.birthday = self.cleaned_data["birthday"]
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user


class CustomSocialAccountSignUp(SocialAccountSignUpForm):
    def __init__(self, *args, **kwargs):
        super(CustomSocialAccountSignUp, self).__init__(*args, **kwargs)
        custom_form = CustomUserCreationForm()
        self.fields.update(custom_form.fields)
        self.fields.pop("password1", None)
        self.fields.pop("password2", None)

    def save(self, request):
        user = super(CustomSocialAccountSignUp, self).save(request)
        user.username = self.cleaned_data["username"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.photo = self.cleaned_data["photo"]
        user.birthday = self.cleaned_data["birthday"]
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


class CustomChangePasswordForm(forms.Form):
    oldpassword = forms.CharField(required=True, widget=forms.PasswordInput(attrs={"placeholder": "Old Password"}))
    password1 = forms.CharField(required=True, widget=forms.PasswordInput(), label="Set New Password")
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(), label="Confirm New Password")

    class Meta:
        model = CustomUser
        field = ("oldpassword", "password1", "password2")


class CustomPasswordAccountChangeForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordAccountChangeForm, self).__init__(*args, **kwargs)
        custom_form = CustomChangePasswordForm()
        self.fields.update(custom_form.fields)


class CustomPasswordAccountSetForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordAccountSetForm, self).__init__(*args, **kwargs)
        custom_form = CustomChangePasswordForm()
        self.fields.update(custom_form.fields)
        self.fields.pop("oldpassword", None)


class CustomPasswordAccountResetForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordAccountResetForm, self).__init__(*args, **kwargs)
        custom_form = CustomChangePasswordForm()
        self.fields.update(custom_form.fields)
        self.fields.pop("oldpassword", None)


class PublishForm(forms.ModelForm):
    attached_url = forms.URLField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    context = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control"}), required=True)
    title = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "value": "No title"}), required=True)

    class Meta:
        model = Publication
        fields = ["title", "context", "attached_file", "attached_url"]

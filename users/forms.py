from allauth.account.forms import SignupForm, ChangePasswordForm, SetPasswordForm, ResetPasswordKeyForm
from allauth.socialaccount.forms import SignupForm as SocialAccountSignUpForm
from django import forms
from django.contrib.auth.forms import UserChangeForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from app.constants import FILE_MAX_SIZE
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
    class Meta:
        model = Publication
        fields = ["author_id", "title", "context", "attached_image", "attached_file"]
        labels = {
            "title": "Publication headline",
            "context": "Description",
        }

    def __init__(self, *args, **kwargs):
        super(PublishForm, self).__init__(*args, **kwargs)
        self.fields["author_id"].widget = forms.HiddenInput()
        self.fields["author_id"].initial = kwargs.get("initial", {}).get("author_id")

    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) > 255:
            raise forms.ValidationError("Title is too long")
        elif len(title) == 0:
            title = "No title"
        return title

    def clean_context(self):
        context = self.cleaned_data["context"]
        if len(context) == 0:
            raise forms.ValidationError("Context cannot be empty")
        elif len(context) < 10:
            raise forms.ValidationError("Please add more details to the contex")
        # elif all(chr(context.isdigit())):
        #     raise forms.ValidationError("Context cannot consist only of numbers")

        return context

    def clean_attached_image(self):
        image = self.cleaned_data["attached_image"]
        if image:
            if image.size > FILE_MAX_SIZE:
                raise forms.ValidationError("The image size must be less than 2 megabytes")

        return image

    def clean_attached_file(self):
        file = self.cleaned_data["attached_file"]
        if file:
            if file.size > FILE_MAX_SIZE:
                raise forms.ValidationError("The file size must be less than 2 megabytes")

        return file

from django import forms

from core.helpers import form_check_len
from community.models import Community, BlackList
from users.models import Moderators


class CreateCommunityForm(forms.ModelForm):
    is_private = forms.ChoiceField(choices=[(True, "Private"), (False, "Public")], label="Status")

    class Meta:
        model = Community
        fields = ["name", "description", "is_private"]


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "description", "is_private"]


class BlackListForm(forms.ModelForm):
    class Meta:
        model = BlackList
        fields = ["user", "community", "reason"]
        labels = {"reason": "Describe the reason for the ban"}
        widgets = {
            "reason": forms.Textarea(
                attrs={
                    "placeholder": "The description of the reason must be at minimum 50 or maximum 2000 characters long"
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super(BlackListForm, self).__init__(*args, **kwargs)
        self.fields["user"].widget = forms.HiddenInput()
        self.fields["user"].initial = kwargs.get("initial", {}).get("user")
        self.fields["community"].widget = forms.HiddenInput()
        self.fields["community"].initial = kwargs.get("initial", {}).get("community")

    def clean_reason(self):
        reason = self.cleaned_data["reason"]
        too_short_error = "Please add more details to the reason"
        too_long_error = "The reason is too long"
        return form_check_len(reason, 50, 2000, too_short_error, too_long_error)


class PrivilegesForm(forms.ModelForm):
    class Meta:
        model = Moderators
        fields = ["user", "is_owner", "is_admin", "is_moderator"]

    def __init__(self, *args, **kwargs):
        super(PrivilegesForm, self).__init__(*args, **kwargs)
        self.fields["user"].widget = forms.HiddenInput()
        self.fields["user"].initial = kwargs.get("initial", {}).get("user")

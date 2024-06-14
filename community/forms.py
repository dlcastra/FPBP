from django import forms

from community.models import Community


class CreateCommunityForm(forms.ModelForm):
    is_private = forms.ChoiceField(choices=[(True, "Private"), (False, "Public")], label="Status")

    class Meta:
        model = Community
        fields = ["name", "description", "is_private"]


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "description", "is_private"]

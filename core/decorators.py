from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from users.models import Moderators


def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        owner = get_object_or_404(Moderators, is_owner=True)
        is_owner = Moderators.objects.filter(user=request.user, user__username=owner).exists()

        if is_owner:
            return view_func(request, *args, **kwargs)
        else:
            return redirect("community", name=kwargs["name"])

    return _wrapped_view

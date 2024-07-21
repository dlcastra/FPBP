from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from users.models import Moderators


def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        is_owner = Moderators.objects.filter(user=user, is_owner=True).exists()
        is_admin = Moderators.objects.filter(user=user, is_admin=True).exists()
        is_moderator = Moderators.objects.filter(user=user, is_moderator=True).exists()
        # try:
        #     owner = get_object_or_404(Moderators, is_owner=True, user_id=request.user.id)
        #     is_owner = Moderators.objects.filter(user=request.user, user__username=owner).exists()
        # except Moderators.DoesNotExist:
        #     is_owner = False
        #
        # try:
        #     admin = get_object_or_404(Moderators, is_admin=True, user_id=request.user.id)
        #     is_admin = Moderators.objects.filter(user=request.user, user__username=admin).exists()
        # except Moderators.DoesNotExist:
        #     is_admin = False
        #
        # try:
        #     moderator = get_object_or_404(Moderators, is_moderator=True, user_id=request.user.id)
        #     is_moderator = Moderators.objects.filter(user=request.user, user__username=moderator).exists()
        # except Moderators.DoesNotExist:
        #     is_moderator = False

        if is_owner or is_admin or is_moderator:
            return view_func(request, *args, **kwargs)
        else:
            return redirect("community", name=kwargs["name"])

    return _wrapped_view

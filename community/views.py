import json

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import ListView

from app.models import Notification
from community.forms import CreateCommunityForm, BlackListForm
from community.models import Community, CommunityFollowers, CommunityFollowRequests, BlackList
from core.decorators import owner_required
from core.helpers import base_post_method
from core.mixins import ViewWitsContext
from users.forms import PublishForm
from users.models import Moderators, Publication


class CreateCommunityView(View):
    template_name = "community/create_community.html"
    form_class = CreateCommunityForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            community = form.save(commit=True)
            moderator = Moderators.objects.create(user=request.user, is_owner=True)
            community.admins.add(moderator)
            return redirect(f"/community/name-{form.cleaned_data['name']}/")

        else:
            return render(request, self.template_name, {"form": form})


class CommunityListView(ListView):
    model = Community
    template_name = "community/community_list.html"


class CommunityView(ViewWitsContext):
    """
    A view handler for displaying and interacting with the main community page.
    """

    template_name = "community/community_detail/community_main_page.html"

    def get_context_data(self, request, **kwargs):
        """
        :return: Dictionary context:
            - publication_form (form): Publication form with initial author
            - name (str): Community name taken from URL
            - community_data (model instance): Community instance
            - community_followers (list): List of subscribed followers
            - is_follow_user (bool): True if user is followed by community, False otherwise
            - author_id (int): Publication author's ID
        """
        context = super().get_context_data(request, **kwargs)
        name = self.kwargs.get("name")
        community_data = Community.objects.get(name=name)

        # PUBLICATION DATA
        author_id = community_data.admins.get(is_owner=True).user.id
        publication_form = PublishForm(initial={"author_id": author_id})
        is_owner = Moderators.objects.filter(user=self.request.user, is_owner=True).exists()

        # FOLLOWERS DATA
        community_followers = CommunityFollowers.objects.filter(community=community_data, is_follow=True).all()
        is_follow_user = CommunityFollowers.objects.filter(
            community=community_data, is_follow=True, user=self.request.user.id
        ).all()
        request_status = CommunityFollowRequests.objects.filter(
            community=community_data, user=self.request.user.id
        ).all()

        # CONTEXT
        context["publication_form"] = publication_form
        context["name"] = name
        context["community_data"] = community_data
        context["community_followers"] = community_followers
        context["is_follow_user"] = is_follow_user
        context["request_status"] = request_status
        context["is_owner"] = is_owner
        context["author_id"] = author_id
        return context

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests, renders the community page with the appropriate context.

        :param request: None
        :param args: Additional arguments.
        :param kwargs: Expects user id from request

        :return: Render template with community context:
            - follow_value (str): Returns Unfollow if the user has already subscribed, otherwise returns Follow
        :used context from get_context_data:
            - is_follow_user (int): request user id
        """
        context = self.get_context_data(request, **kwargs)
        context["follow_value"] = "Unfollow" if context["is_follow_user"].exists() else "Follow"
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handles subscribing and unsubscribing from the community, sending subscription requests,
        and creating community publications.

        :param request: HTTP request object that can include '?new_post'
        or 'follow', 'unfollow', 'send_request' and 'remove_request' from actions

        :param args: Additional arguments.
        :param kwargs: Expects 'name' as a string taken from the URL.

        :return: JsonResponse, redirect to another class method or redirect to community home page:
            - If action is 'follow' or 'unfollow': redirect to handle_send_request_action
            - If action is 'send_request' or 'remove_request' end with success: {"success": true}
            - If action is 'send_request' or 'remove_request' end without success: redirect to handle_send_request_action
            - If param is 'new_post' and form is valid: redirect to community home page
            - If param is 'new_post' and form is not valid: {"message": "Something went wrong"}
            - For other ways: redirect to community home page
        :used context from get_context_data:
            - community_data (model instance): Community name
            - author_id (int): Request user id if user is community owner
        """
        # CONTEXT VARIABLES
        context = self.get_context_data(request, **kwargs)
        community_data = context["community_data"]
        action = self.request.POST.get("action")
        user = self.request.user.id

        # FOLLOW REQUESTS
        if action == "follow" or action == "unfollow":
            return self.handle_follow_action(context)
        elif action == "send_request" or action == "remove_request":
            request_obj = CommunityFollowRequests.objects.filter(community=community_data, user=user, send_status=True)
            if request_obj.exists():
                request_obj.delete()
                return JsonResponse({"success": True})
            else:
                return self.handle_send_request_action(context)

        # POST CREATION REQUEST
        elif "new_post" in request.POST and context["is_owner"]:
            form = PublishForm(request.POST, request.FILES, initial={"author_id": context["author_id"]})
            if form.is_valid:
                publication = form.save(commit=False)
                publication.content_type = ContentType.objects.get_for_model(Community)
                publication.save()
                form.save()
                community_data.posts.add(publication)

                return redirect(f"/community/name-{context.get('name')}/")

        else:
            messages.error(request, "Something went wrong")

        return redirect(f"/community/name-{context.get('name')}/")

    def handle_follow_action(self, context: dict) -> JsonResponse:
        """
        This function changes the user's subscription status to the community.
        If a user is already subscribed, the function unsubscribes him/her, and vice versa.
        After changing the status, function returns the number of subscribers and the current subscription status.

        :param context: A dictionary with context data containing information about the community.
        :return: Json response with context:
            - followers_count (int): Number of community followers
            - is_following (bool): True if user is subscribed, otherwise False
        """
        community = context.get("community_data")
        follower_obj, created = CommunityFollowers.objects.get_or_create(user=self.request.user, community=community)
        follower_obj.is_follow = not follower_obj.is_follow
        follower_obj.save()
        followers_count = CommunityFollowers.objects.filter(community=community, is_follow=True).count()
        return JsonResponse(
            {
                "followers_count": followers_count,
                "is_following": follower_obj.is_follow,
            }
        )

    def handle_send_request_action(self, context: dict) -> JsonResponse:
        """
        This function is responsible for sending subscription requests to the community.
        When a user sends a request, a notification is sent to the community administrators.

        :param context: A dictionary with context data containing information about the community.
        :return: Json response with context:
            - request_status (bool): Try if was sent successfully
        """
        community = context.get("community_data")
        request_obj, created = CommunityFollowRequests.objects.get_or_create(
            user=self.request.user, community=community
        )

        if not request_obj.send_status:
            follow_request_link = reverse("community_followers_requests", kwargs={"name": community.name})
            message = mark_safe(
                f"There is your new follow request: {request_obj.user.username}\n"
                f'Check your follow request list: <a href="{follow_request_link}">Request List</a>.'
            )
            Notification.objects.create(user=community.admins.get(is_owner=True).user, message=message)

            request_obj.send_status = True
        request_obj.save()

        return JsonResponse(
            {
                "request_status": request_obj.send_status,
            }
        )


class CommunityFollowersListView(ListView):
    model = CommunityFollowers
    template_name = "community/community_detail/community_followers/community_followers.html"

    def get_queryset(self):
        community = get_object_or_404(Community, name=self.kwargs["name"])
        followers = CommunityFollowers.objects.filter(community=community, is_follow=True).all()
        return followers


class FollowersRequestListView(View):
    template_name = "community/community_detail/community_followers/follow_requests.html"

    def get_context_data(self, **kwargs):
        """
        :param kwargs: Community name taken from URL
        :return: Dictionary with list users whose subscription requests were not accepted
        """
        community = get_object_or_404(Community, name=self.kwargs["name"])
        followers = CommunityFollowRequests.objects.filter(community=community, accepted=False, send_status=True).all()
        return {"communityfollowers_list": followers}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Processes POST requests to accept or reject community subscription requests.
        If the request is an AJAX request, the function performs the following actions depending
        on the value of the "action" parameter in the POST request:
            - "accept": Accepts the subscription request and adds the user to the community subscriber list.
            - "reject": Rejects the subscription request.

        :param request:
        :param args: Additional arguments.
        :param kwargs: Community name taken from URL

        :return: Json response confirming successful completion of the action.
            - (dict): {"success": "ok"}
        """

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            community = get_object_or_404(Community, name=self.kwargs["name"])
            user_id = request.POST.get("user")
            accept_obj = CommunityFollowRequests.objects.get(
                community=community, user=user_id, accepted=False, send_status=True
            )
            if request.POST.get("action") == "accept":
                accept_obj.delete()
                follow_r_obj, created = CommunityFollowers.objects.get_or_create(
                    user=accept_obj.user, community=community
                )
                follow_r_obj.is_follow = True
                follow_r_obj.save()
            elif request.POST.get("action") == "reject":
                accept_obj.delete()

        return JsonResponse({"success": "ok"})


class AdminPanelView(ViewWitsContext):
    """
    View to administrate community data and community users
    """

    template_name = "community/community_detail/admin_panel/adminpanel.html"

    """
    What needs to be added:
        1. Granting privileges (admin or moderator)
        2. Removal of privileges
        3. View recent activity
        4. Possibility to delete/hide posts
    """

    def get_context_data(self, request, **kwargs):
        """
        :return: Dictionary context:
            - owner (str): Owner username
            - admins (list) or (str): If there are administrators in the community, a list will be returned,
            otherwise a message "You have no admins yet" will be returned
            - admins (list) or (str): If there are moderators in the community, a list will be returned,
            otherwise a message "You have no moderators yet" will be returned
            - instance (str): Community instance name
            - community_id (int): Community id
            - followers_count (int): Number of subscribed users
            - all_posts (list): List of all community posts
        """
        context = super().get_context_data(request)
        instance = get_object_or_404(Community, name=self.kwargs["name"])

        # COMMUNITY MANAGERS DATA
        context["owner"] = get_object_or_404(Moderators, is_owner=True)
        context["admins"] = Moderators.objects.filter(is_admin=True)
        context["moderators"] = Moderators.objects.filter(is_moderator=True)

        if not context["admins"]:
            context["admins"] = "You have no admins yet"
        if not context["moderators"]:
            context["moderators"] = "You have no moderators yet"

        # COMMUNITY BASE DATA
        context["instance"] = instance
        context["community_id"] = Community.objects.get(name=self.kwargs["name"]).id
        context["followers_count"] = CommunityFollowers.objects.filter(community=instance, is_follow=True).count()

        # context["last_actions"] = ...

        # GET COMMUNITY PUBLICATIONS
        owner = instance.admins.filter(is_owner=True).first()
        if owner:
            context["all_posts"] = list(Publication.objects.filter(author_id=owner.user.id).values())
        else:
            context["all_posts"] = "You don't have any publication, but you can change that right now!"

        return context

    """ -------- BASE METHODS: Call a specific function depending on the keyword -------- """

    @method_decorator(owner_required)
    def get(self, request, *args, **kwargs):
        """
        Pointing method to other views or actions

        :param request: HTTP request object that can include '?followers_list' or '?edit' in the query parameters.
        :param args: Additional arguments.
        :param kwargs: Expects 'name' as a string taken from the URL.

        :return: Redirect to other views or render view template
            - If param request is 'edit': render edit_template
            - If param request is 'followers_list': redirect to the BlackListView view where all users will be displayed
            - For other ways: render view base template
        """
        context = self.get_context_data(request, **kwargs)

        if "edit" in request.GET:
            edit_template = "community/create_community.html"
            form = CreateCommunityForm(instance=context["instance"])
            return render(request, edit_template, {"form": form})

        if "followers_list" in request.GET:
            return redirect("blacklist/")

        return render(request, self.template_name, context)

    @method_decorator(owner_required)
    def post(self, request, *args, **kwargs):
        """
        Pointing method to other views or actions

        :param request: HTTP request object that can include '?put_ban' or '?remove_ban' in the query parameters.
        And 'XMLHttpRequest' in request headers.
        :param args: Additional arguments.
        :param kwargs: Expects 'name' as a string taken from the URL.

        :return: Redirect to other views or render:
            - If request without any params: redirect to self

            - If param request is 'put_ban' and request headers is 'XMLHttpRequest':
            redirect to BlackListView with param 'put_ban'

            - If param request is 'remove_ban': redirect to BlackListView with param 'remove_ban'
        """
        context = self.get_context_data(request, **kwargs)

        # CONTEXT VARIABLES
        form = CreateCommunityForm(request.POST, instance=context["instance"])
        edit_template = "community/create_community.html"
        redirect_url = request.path_info
        redirect_response = base_post_method(form, redirect_url)

        if redirect_response:  # To edit community data
            return redirect_response

        request_headers = request.headers.get("X-Requested-With")
        request_action = json.loads(request.body)["action"]
        if request_headers == "XMLHttpRequest" and request_action == "put_ban":  # To ban a user
            return redirect("blacklist", name=self.kwargs["name"])

        if "remove_ban" in request.POST:  # To unban a user
            return redirect("blacklist", name=self.kwargs["name"])

        return render(request, edit_template, {"form": form})


class BlackListView(ViewWitsContext):
    """
    View to ban users in community
    """

    class_form = BlackListForm
    template_name = "community/community_detail/admin_panel/users_list.html"

    def get_context_data(self, request, **kwargs):
        """
        :return: Dictionary context:
        - black_list (list): List of blacklisted users
        - banned_users (list[dict[int, int, str, str]]): Info about the banned users
            - id (int): User id
            - blacklist_id (int): Database record ID
            - username (str): User username
            - reason (str): Reason why the user was blacklisted
        - followers (list) List of subscribed users
        - community (str): Community instance name
        """
        context = super().get_context_data(request)
        # Special variables
        community = get_object_or_404(Community, name=self.kwargs["name"])
        followers = CommunityFollowers.objects.filter(community=community, is_follow=True)
        banned_user_list = [banned_user.user.id for banned_user in BlackList.objects.filter(community=community)]

        # Context variables
        context["black_list"] = BlackList.objects.filter(community=community).select_related("user__user")
        banned_users = [
            {
                "id": entry.user.id,
                "blacklist_id": entry.id,
                "username": entry.user.user.username,
                "reason": entry.reason,
            }
            for entry in context["black_list"]
        ]
        context["banned_users"] = banned_users
        context["followers"] = []
        for follower in followers:
            if follower.user.id not in banned_user_list:
                context["followers"].append(follower)
            elif not banned_user_list:
                context["followers"] = followers
        context["community"] = community

        return context

    def get(self, request, *args, **kwargs):
        """
        Return data about banned users in a community.

        :param request: None
        :param args: Additional arguments.
        :param kwargs: Expects 'name' as a string taken from the URL.

        :return: Rendered HTTP response with the following context:
            - banned_users (list): List of banned users.
            - instance (Community): Instance of the Community.
            - followers (list): List of followers.
            - csrf_token (str): CSRF token for the request.
        """
        context = self.get_context_data(request, **kwargs)
        return render(
            request,
            self.template_name,
            {
                "banned_users": context["banned_users"],
                "instance": context["community"],
                "followers": context["followers"],
                "csrf_token": get_token(request),
            },
        )

    @method_decorator(owner_required)
    def post(self, request, *args, **kwargs):
        """
        Redirects data in functions depending on the selected action to pages

        :param request: To ban user '?put_ban', to remove user from black list '?remove_ban'
        :param args: Additional arguments.
        :param kwargs: Expects 'user_id' as int taken from the query parameters.

        :return: Return JsonResponse in case of bad request.
        """
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            data = json.loads(request.body)
            print(data)
            action = data.get("action")
            if action == "put_ban":
                return self.ban_user(request, data)
            if action == "remove_ban":
                return self.delete_user_from_blacklist(request, data)

        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    @staticmethod
    def ban_user(request, data: json):
        """
        Places the user in the community_blacklist table.
        If the user is already in the blacklist, the reason is updated.

        :param request: None
        :param data: JSON object containing the necessary data:
            - follower_id (int): ID of the follower to be banned.
            - reason (str): Reason for banning the user.
            - instance (str): Name of the community.

        :return: JsonResponse indicating the success or failure of the operation:
            - If the user is successfully banned or upgraded:
            {"status": "success"}

            - If one of the required components has been lost or not specified:
            {"status": "error", "message": "Missing follower_id, reason, or instance name"} and status code 400

            - If JSON was invalid:
            {"status": "error", "message": "Invalid JSON"} and status code 400

            - In case of other errors:
            {"status": "error", "message": Exception error body} and status code 400
        """
        try:
            follower_id: int = data.get("follower_id")
            reason: str = data.get("reason")
            instance_name: str = data.get("instance")

            # Check data from JSON response
            if follower_id and reason and instance_name:
                community = get_object_or_404(Community, name=instance_name)
                blacklist, created = BlackList.objects.get_or_create(
                    user_id=follower_id, community=community, defaults={"reason": reason}
                )
                if not created:
                    blacklist.reason = reason
                    blacklist.save()
                return JsonResponse({"status": "success"})

            return JsonResponse(
                {"status": "error", "message": "Missing follower_id, reason, or instance name"}, status=400
            )

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    @staticmethod
    def delete_user_from_blacklist(request, data: json):
        """
        Delete the user from the community_blacklist table.

        :param request: None
        :param data: Data from JSON response:
            - user_id (int): The id of the user from community_blacklist table.

        :return: JsonResponse indicating the success or failure of the operation:
            - If the user is successfully deleted:
            {"status": "success"}

            - In other cases:
            {"status": "error", "message": Exception error body} and status code 400
        """
        try:
            banned_user_id: int = data.get("bannedUserId")
            print(f"CSRF Token: {request.headers.get('X-CSRFToken')}")
            print(f"Banned User ID: {banned_user_id}")

            blacklist_user = get_object_or_404(BlackList, user_id=banned_user_id)
            blacklist_user.delete()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

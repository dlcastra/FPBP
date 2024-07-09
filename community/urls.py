from django.urls import path

from community import views

urlpatterns = [
    path("create/", views.CreateCommunityView.as_view(), name="create_community"),
    path("name-<str:name>/", views.CommunityView.as_view(), name="community"),
    path("all/", views.CommunityListView.as_view(), name="community_list"),
    path("name-<str:name>/followers/", views.CommunityFollowersListView.as_view(), name="community_followers"),
    path(
        "name-<str:name>/followers/requests/",
        views.FollowersRequestListView.as_view(),
        name="community_followers_requests",
    ),
    path("name-<str:name>/admin-panel/", views.AdminPanelView.as_view(), name="admin_panel"),
    path(
        "name-<str:name>/admin-panel/users-management/",
        views.UsersManagementView.as_view(),
        name="users_management",
    ),
]

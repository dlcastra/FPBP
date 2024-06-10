from django.urls import path

from app import views

urlpatterns = [
    path("", views.MainPageView.as_view(), name="index"),
    # URLS FOR THREADS
    path("threads/", views.ThreadsPageView.as_view(), name="threads"),
    path("new-thread/", views.CreateThreadView.as_view(), name="new_thread"),
    path("thread-detail/<int:pk>", views.ThreadDetailView.as_view(), name="detail"),
    path(
        "post-comments-t/<int:pk>/<int:content_type_id>/",
        views.ThreadCommentsHandlerView.as_view(),
        name="post_feedback",
    ),
    path("remove-comments-t/<int:answer_id>/", views.RemoveCommentThread.as_view(), name="remove_answer"),
    # URLS FOR PROG LANGUAGES
    path("tutorials/<str:slug>/<int:page_id>/", views.TutorialPageView.as_view(), name="tutorials"),
    # COMMUNITY URLS
    path("communitys/", views.CommunityListView.as_view(), name="community_list"),
    path("create-community/", views.CreateCommunityView.as_view(), name="create_community"),
    path("community/<name>/", views.CommunityView.as_view(), name="community"),
    # RECOMMENDATIONS URLS
    path("recommendations/", views.RecommendationFeedView.as_view(), name="recommendations"),
]

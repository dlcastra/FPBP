from django.urls import path

from app import views

urlpatterns = [
    path("", views.MainPageView.as_view(), name="index"),
    # URLS FOR THREADS
    path("threads/", views.ThreadsPageView.as_view(), name="threads"),
    path("new-thread/", views.CreateThreadView.as_view(), name="new_thread"),
    path("thread-detail/<int:pk>", views.ThreadDetailView.as_view(), name="detail"),
    path("remove-comments-t/<int:answer_id>/", views.RemoveCommentThread.as_view(), name="remove_answer"),
    # URLS FOR PROG LANGUAGES
    path("tutorials/<str:slug>/<int:page_id>/", views.TutorialPageView.as_view(), name="tutorials"),
    # RECOMMENDATIONS URLS
    path("recommendations/", views.RecommendationFeedView.as_view(), name="recommendations"),
    # SEARCH URLS
    path("search/", views.SearchView.as_view(), name="search"),
    path("search/autocmplete/", views.AutocompleteSearchView.as_view(), name="autocomplete"),
]

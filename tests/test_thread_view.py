import pytest
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from app.models import Thread
from users.models import CustomUser


@pytest.mark.django_db
class TestThreadViews(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(username="testuser1", email="test@test.com", password="testpas")
        self.user2 = CustomUser.objects.create_user(username="testuser2", email="test@test.com", password="testpas")
        self.client = Client()
        self.url = reverse("threads")
        self.first_thread = Thread.objects.create(
            id=1,
            title="title_first_thread",
            context="content",
            author_id=self.user1.id,
            published_at="2024-06-12",
            status="published",
        )
        self.second_thread = Thread.objects.create(
            id=2,
            title="title_second_thread",
            context="content",
            author_id=self.user1.id,
            published_at="2024-06-12",
            status="published",
        )

    def test_get_request_on_thread_page(self):
        response = self.client.get(self.url)
        context = response.context
        expected_threads = Thread.objects.order_by("-id")

        # POSITIVE RESULTS
        assert response.status_code == status.HTTP_200_OK
        assert "threads" in context
        assert "search_query" in context
        assert list(context["threads"]) == list(expected_threads)
        self.assertTemplateUsed("threads/all_threads/threads_page.html")

        # NEGATIVE RESULTS
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED
        assert list(context["threads"]) != []

    def test_search_query(self):
        search_term = "title_first_thread"

        response = self.client.get(self.url, {"search_query": search_term})

        # POSITIVE RESULTS
        assert response.status_code == status.HTTP_200_OK

        # NEGATIVE RESULTS
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_thread_details(self):
        url = reverse("detail", kwargs={"pk": self.first_thread.id})

        response = self.client.get(url)
        context = response.context
        model_detail = context["model_detail"]

        # POSITIVE RESULTS
        assert response.status_code == status.HTTP_200_OK
        assert model_detail.id == self.first_thread.id
        assert model_detail.title == self.first_thread.title
        assert model_detail.context == self.first_thread.context
        self.assertTemplateUsed("threads/threads_detail/thread_detail.html")

        # NEGATIVE RESULTS
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_thread(self):
        self.client.force_login(user=self.user1)
        url = reverse("detail", kwargs={"pk": self.first_thread.id})
        data = {
            "id": 1,
            "title": "title_first_thread",
            "context": "updated content",
            "author_id": 1,
            "published_at": "2024-06-12",
            "status": "published",
        }

        response = self.client.post(url, data)
        context = response.context
        model_detail = context["model_detail"]

        assert response.status_code == status.HTTP_200_OK
        print(model_detail.context)
        # assert model_detail.context == data["context"]

    def test_methods_not_allowed(self):
        all_threads_url = reverse("threads")
        thread_detail_url = reverse("detail", kwargs={"pk": self.first_thread.id})

        methods = ["put", "patch", "delete"]
        urls = [all_threads_url, thread_detail_url]
        response_list = []
        response_post = self.client.post(all_threads_url)

        for url in urls:
            for method in methods:
                client_method = getattr(self.client, method)
                response = client_method(url)
                response_list.append(response)

        for response in response_list:
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        assert response_post.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

import json
from urllib.parse import urlencode
import pytest
from bs4 import BeautifulSoup
from django.middleware.csrf import get_token
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from rest_framework import status

from app.forms import ThreadForm
from app.models import Thread
from users.models import CustomUser


@pytest.mark.django_db
class TestThreadViews(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(username="testuser1", email="test@test.com", password="testpas")
        self.user2 = CustomUser.objects.create_user(username="testuser2", email="test@test.com", password="testpas")
        self.client = Client()
        self.factory = RequestFactory()
        self.get_url = reverse("threads")
        self.post_url = reverse("new_thread")
        self.first_thread = Thread.objects.create(
            id=1,
            title="title_first_thread",
            context="content",
            author=self.user1,
            published_at="2024-06-12",
            status="published",
        )
        self.second_thread = Thread.objects.create(
            id=2,
            title="title_second_thread",
            context="content",
            author=self.user1,
            published_at="2024-06-12",
            status="published",
        )

    def test_get_request_on_thread_page(self):
        response = self.client.get(self.get_url)
        context = response.context
        expected_threads = Thread.objects.order_by("-id")

        # POSITIVE RESULTS
        assert response.status_code == status.HTTP_200_OK
        assert "threads" in context
        assert "search_query" in context
        assert list(context["threads"]) == list(expected_threads)
        self.assertTemplateUsed(response, "threads/all_threads/threads_page.html")

        # NEGATIVE RESULTS
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED
        assert list(context["threads"]) != []

    def test_search_query(self):
        search_term = "title_first_thread"

        response = self.client.get(self.get_url, {"search_query": search_term})

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
        self.assertTemplateUsed(response, "threads/threads_detail/thread_detail.html")

        # NEGATIVE RESULTS
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_thread(self):
        self.client.force_login(self.user1)

        # Simulate a GET request with the "edit" parameter
        url = reverse("detail", kwargs={"pk": self.first_thread.id})
        response = self.client.get(f"{url}?edit=Edit")

        # Check if the edit template is rendered
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'threads/threads_detail/edit_thread.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].instance, self.first_thread)

        # Simulate a POST request to update the thread
        update_data = {
            'title': 'updated_title',
            'context': 'updated_contextxcvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv',
            'author': self.user1.id,
        }
        response = self.client.post(url, data=update_data)

        # Print form errors if the response is not a redirect
        if response.status_code != status.HTTP_302_FOUND:
            form_errors = response.context['form'].errors
            print("Form Errors:", form_errors)

        self.first_thread.refresh_from_db()

        # Check if the thread was updated and redirected correctly
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(self.first_thread.title, 'updated_title')
        self.assertEqual(self.first_thread.context,
                         'updated_contextxcvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')

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

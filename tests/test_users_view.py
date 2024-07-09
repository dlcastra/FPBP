from unittest.mock import patch

import pytest
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialAccount
from bs4 import BeautifulSoup
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.urls import reverse

from app.models import Comments
from users.models import CustomUser, Publication


@pytest.mark.django_db
class TestUsersView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_model = CustomUser
        self.user = CustomUser.objects.create_user(username="user", password="password", email="<EMAIL>")
        self.user1 = CustomUser.objects.create_user(username="user1", password="password", email="<EMAIL>")
        self.social_account = SocialAccount.objects.create(user=self.user, provider="google", uid="12345")

    def test_register_user(self, email="testuser@gmail.com", password="testPassword!"):
        url = reverse("account_signup")
        data = {
            "email": email,
            "password1": password,
            "password2": password,
            "first_name": "firstname",
            "last_name": "last_name",
            "birthday": "1900-01-01",
            "username": "test_user",
            "action": "signup",
        }
        response = self.client.post(url, data)
        soup = BeautifulSoup(response.content, "html.parser")
        print(soup)
        self.assertEqual(response.status_code, 302)
        user_created = self.user_model.objects.filter(email=email, username="test_user").exists()
        self.assertTrue(user_created)

    def test_user_page(self):
        self.client.force_login(self.user)
        url = reverse("user_page", kwargs={"username": self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        username = soup.find("label", {"id": "username"})
        follow_btn = soup.find("button", {"id": "follow-button"})
        self.assertIsNone(follow_btn)
        self.assertEqual(username.text, str(self.user.username))
        self.client.force_login(self.user1)
        url = reverse("user_page", kwargs={"username": self.user.username})
        data = {
            "user": self.user,
            "action": "follow",
            "is_following": False,
        }
        self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        follow_btn = soup.find("button", {"id": "follow-button"})
        self.assertIn(
            "Unfollow",
            follow_btn.text,
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_change_user_data(self):
        self.client.force_login(self.user)
        url = reverse("socialaccount_connections")
        data = {
            "user": self.user,
            "username": "new_username",
            "first_name": "new_first_name",
            "last_name": "new_last_name",
            "birthday": "1900-01-01",
            "email": "newemail@gmail.com",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        print(soup)
        username = soup.find("input", {"id": "id_username"})
        first_name = soup.find("input", {"id": "id_first_name"})
        last_name = soup.find("input", {"id": "id_last_name"})
        birthday = soup.find("input", {"id": "id_birthday"})
        email = soup.find("input", {"id": "id_email"})
        self.assertEqual(username["value"], data["username"])
        self.assertEqual(first_name["value"], data["first_name"])
        self.assertEqual(last_name["value"], data["last_name"])
        self.assertEqual(birthday["value"], data["birthday"])
        self.assertEqual(email["value"], data["email"])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_user_connections(self):
        self.client.force_login(self.user)
        url = reverse("google_login")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)


@pytest.mark.django_db
class DisconnectAccountTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.social_account = SocialAccount.objects.create(user=self.user, provider="google", uid="12345")
        self.client.login(username="testuser", password="password123")
        self.disconnect_url = reverse("disconnect_account", kwargs={"provider": "google"})

    def test_user_connections(self):
        self.client.force_login(self.user)
        response = self.client.post(self.disconnect_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})
        response = self.client.post(self.disconnect_url)
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content, {"error": "Account not found."})
        response = self.client.get(self.disconnect_url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "Invalid request method."})
        with patch("allauth.socialaccount.models.SocialAccount.objects.get") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")
            response = self.client.post(self.disconnect_url)
            self.assertEqual(response.status_code, 500)
            self.assertJSONEqual(response.content, {"error": "Unexpected error"})


@pytest.mark.django_db
class PublicationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username="testuser", email="test@example.com")
        self.publication = Publication.objects.create(
            content_type=ContentType.objects.get_for_model(Publication),
            author_id=self.user.id,
            title="Title",
            context="Context",
        )
        self.publication.save()

    def test_create_publication(self):
        self.client.force_login(self.user)
        url = reverse("new_publication", kwargs={"username": self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = {
            "author_id": self.user.id,
            "title": "New Post",
            "context": "updated_contextxcvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
            "new_post": "new_post",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_publication_details(self):
        self.client.force_login(self.user)
        url = reverse("user_publication", kwargs={"pk": self.publication.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.get(url, data={"edit": "Edit"})
        self.assertTemplateUsed("publications/publication_detail/edit_publication.html")
        data = {
            "title": "updated_title",
            "context": "updated_contextxcvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
            "author_id": self.user.id,
        }
        response = self.client.post(f"{url}?edit=Edit", data)
        self.assertEqual(response.status_code, 302)


class TestCommentsView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username="testuser", email="test@example.com")
        self.publication = Publication.objects.create(
            content_type=ContentType.objects.get_for_model(Publication),
            author_id=self.user.id,
            title="Title",
            context="Context",
        )
        self.publication.save()
        self.comment = Comments.objects.create(
            content_type=ContentType.objects.get_for_model(Publication),
            object_id=self.publication.id,
            user=self.user,
            title="New Comment",
            context="Context",
        )
        self.comment.save()
        self.template = "publications/publication_detail/answers.html"

    def test_comments(self):
        self.client.force_login(self.user)
        url = reverse("user_publication", kwargs={"pk": self.publication.pk})
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        comment = soup.find_all("span", {"class": "feedback-text"})
        self.assertEqual(len(comment), 1)
        self.assertTemplateUsed(self.template)

    def test_post_comment(self):
        self.client.force_login(self.user)
        url_post = reverse(
            "post_comment_p", kwargs={"pk": self.publication.pk, "content_type_id": self.publication.content_type.id}
        )

        data = {
            "title": "New Comment",
            "feedback": "content",
        }

        response = self.client.post(url_post, data)
        self.assertEqual(response.status_code, 200)

    def test_delete_comment(self):
        self.client.force_login(self.user)
        url = reverse("remove_comment_p", kwargs={"answer_id": self.comment.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comments.objects.filter(pk=self.comment.pk).exists())

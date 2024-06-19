from allauth.socialaccount.models import SocialAccount
from django.test import TestCase, Client
from django.urls import reverse

from users.forms import CustomUserChangeForm
from users.models import CustomUser


class TestCustomUserChangeView(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpas",
            birthday="2000-01-01",
            gender="M",
        )
        self.social_account = SocialAccount.objects.create(
            user=self.user,
            provider="google",
            uid="123456789",
        )
        self.client = Client()
        self.url = reverse("socialaccount_connections")

    def test_get_request(self):
        self.client.login(username="testuser", password="testpas")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/change_user_data.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CustomUserChangeForm)
        self.assertIn("connections", response.context)
        self.assertIn("connected_provider_ids", response.context)

    def test_post_request_valid_data(self):
        self.client.login(username="testuser", password="testpas")
        post_data = {
            "username": "updateduser",
            "email": "updated@test.com",
            "birthday": "2000-01-01",
            "gender": "F",
        }

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/change-data/")

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.email, "updated@test.com")
        self.assertEqual(self.user.gender, "F")

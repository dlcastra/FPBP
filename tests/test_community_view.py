import pytest
from django.test import Client, TestCase
from django.urls import reverse
from bs4 import BeautifulSoup

from app.models import Notification
from community.models import Community, CommunityFollowRequests
from users.models import CustomUser


@pytest.mark.django_db
class TestCommunityView(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = CustomUser.objects.create_user(username="owner", email="<EMAIL>", password="<PASSWORD>")
        self.follower = CustomUser.objects.create_user(username="follower", email="<EMAIL>", password="<PASSWORD>")
        self.private_community = Community.objects.create(
            name="Test Community Private", is_private=True, description=""
        )
        self.private_community.admins.create(user=self.owner, is_owner=True)
        self.private_community.posts.create(
            content_type_id=self.private_community.id, author_id=self.owner.id, title="Test Post", context="Test Post"
        )
        self.private_community.save()
        self.public_community = Community.objects.create(name="Test Community Public", is_private=False, description="")
        self.public_community.admins.create(user=self.owner, is_owner=True)
        self.public_community.posts.create(
            content_type_id=self.private_community.id, author_id=self.owner.id, title="Test Post", context="Test Post"
        )
        self.public_community.save()

    def test_community_list(self):
        self.client.login(username="owner", password="<PASSWORD>")
        response = self.client.get(reverse("community_list"))
        soup = BeautifulSoup(response.content, "html.parser")
        community_list = soup.find(id="community-list")
        self.assertIsNotNone(community_list)
        self.assertIsNotNone(community_list.find_all(id="community-name")[0].text, self.private_community.name)
        self.assertIsNotNone(community_list.find_all(id="community-name")[1].text, self.public_community.name)
        self.assertEqual(response.status_code, 200)

    def test_community_detail_owner(self):
        self.client.login(username="owner", password="<PASSWORD>")
        response_get = self.client.get(reverse("community", kwargs={"name": self.private_community.name}))
        soup = BeautifulSoup(response_get.content, "html.parser")
        community_name = soup.find("h1").text
        community_posts = soup.find_all("a", id="community-post")
        self.assertIsNotNone(community_posts)
        self.assertEqual(community_posts[0].text, self.private_community.posts.first().title)
        self.assertEqual(community_name, self.private_community.name)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, self.private_community.name)

    def test_private_community_detail_follower(self):
        self.client.login(username="follower", password="<PASSWORD>")
        response = self.client.get(reverse("community", kwargs={"name": self.private_community.name}))
        soup = BeautifulSoup(response.content, "html.parser")
        community_name = soup.find("h1").text
        self.assertEqual(community_name, self.private_community.name)
        request_btn = soup.find("button", id="request_btn")
        self.assertIn("Send Request", request_btn.text)
        community_posts = soup.find_all("a", id="community-post")
        self.assertIsNotNone(community_posts, None)
        self.client.post(
            reverse("community", kwargs={"name": self.private_community.name}),
            data={"action": {"send_request": True, "request_status": True}},
        )

        response_post = self.client.post(
            reverse("community", kwargs={"name": self.private_community.name}), data={"action": "send_request"}
        )
        self.assertEqual(response_post.status_code, 200)
        request_exists = CommunityFollowRequests.objects.filter(
            community=self.private_community, user=self.follower
        ).exists()
        self.assertTrue(request_exists)
        response_get_updated = self.client.get(reverse("community", kwargs={"name": self.private_community.name}))
        soup_updated = BeautifulSoup(response_get_updated.content, "html.parser")
        request_btn = soup_updated.find("button", id="request_btn")
        follow_request_link = reverse("community_followers_requests", kwargs={"name": self.private_community.name})
        message = (
            f"There is your new follow request: {self.follower.username}\n"
            f' Check your follow request list: <a href="{follow_request_link}">Request List</a>.'
        )
        notification = Notification.objects.filter(message=message, user=self.owner)
        self.assertIsNotNone(notification)
        self.assertIsNotNone(request_btn)
        self.assertIn("Request already sent", request_btn.text)

import pytest
from django.test import Client, TestCase
from django.urls import reverse
from bs4 import BeautifulSoup
from app.models import Notification
from community.models import Community, CommunityFollowRequests, CommunityFollowers
from community.views import CommunityView
from users.models import CustomUser, Moderators


@pytest.mark.django_db
class TestCommunityView(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = CustomUser.objects.create_user(username="owner", email="<EMAIL>", password="<PASSWORD>")
        self.follower = CustomUser.objects.create_user(username="follower", email="<EMAIL>", password="<PASSWORD>")
        self.follower_request = CustomUser.objects.create_user(
            username="request", email="<EMAIL>", password="<PASSWORD>"
        )
        self.follower_follow = CustomUser.objects.create_user(
            username="follower_follow",
            email="<EMAIL>",
        )
        self.private_community = Community.objects.create(
            name="Test Community Private", is_private=True, description=""
        )
        self.private_community.admins.create(user=self.owner, is_owner=True)
        self.private_community.posts.create(
            content_type_id=self.private_community.id, author_id=self.owner.id, title="Test Post", context="Test Post"
        )
        self.private_community.save()
        self.public_community = Community.objects.create(name="Test Community Public", is_private=False, description="")
        self.moderator = Moderators.objects.create(user=self.owner, is_owner=True)
        self.moderator.save()
        self.public_community.admins.add(self.moderator)
        self.public_community.posts.create(
            content_type_id=self.private_community.id, author_id=self.owner.id, title="Test Post", context="Test Post"
        )
        self.public_community.save()
        self.follow_request = CommunityFollowRequests.objects.create(
            community=self.private_community, user=self.follower_request, accepted=False, send_status=True
        )
        self.follow_request.save()
        self.requests_list = CommunityFollowRequests.objects.filter(
            community=self.private_community, accepted=False, send_status=True
        ).all()
        self.community_follower = CommunityFollowers.objects.create(
            user=self.follower_follow, community=self.public_community, is_follow=True
        )
        self.community_follower.save()
        self.community_follower_list = CommunityFollowers.objects.filter(
            community=self.public_community, is_follow=True
        ).all()

    def test_community_follower_list(self):
        self.client.login(username="owner", password="<PASSWORD>")
        url = reverse("community_followers", kwargs={"name": self.public_community})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_follow_request(self):
        self.client.login(username="owner", password="<PASSWORD>")
        url = reverse("community_followers_requests", kwargs={"name": self.private_community.name})
        self.follow_request.refresh_from_db()

        response = self.client.get(
            url,
            data={
                "communityfollowers_list": self.requests_list,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["communityfollowers_list"][0], self.follow_request)
        data = {
            "user": self.follower_request.id,
            "communityfollowers_list": self.requests_list,
            "action": "accept",
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.requests_list.update()
        assert self.requests_list.count() == 0

    def test_follow_request_r(self):
        self.client.login(username="owner", password="<PASSWORD>")
        self.requests_list.update()
        rqst_follow_url = reverse("community_followers_requests", kwargs={"name": self.private_community.name})
        data = {
            "user": self.follower_request.id,
            "communityfollowers_list": self.requests_list,
            "action": "reject",
        }
        response_post = self.client.post(rqst_follow_url, data=data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response_post.status_code, 200)
        self.requests_list.update()
        assert self.requests_list.count() == 0

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
        self.client.force_login(self.owner)
        get_data = {
            "user": self.owner,
            "is_follow_user": self.follower,
            "community_data": self.public_community,
        }
        url = reverse("community", kwargs={"name": self.public_community.name})
        response_get = self.client.get(url, get_data)
        soup = BeautifulSoup(response_get.content, "html.parser")
        community_name = soup.find("h1").text
        community_posts = soup.find_all("a", id="community-post")
        self.assertIsNotNone(community_posts)
        self.assertEqual(community_posts[0].text, self.public_community.posts.first().title)
        self.assertEqual(community_name, self.public_community.name)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, self.public_community.name)
        data = {
            "title": "New Post",
            "context": "updated_contextxcvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",
            "author_id": self.owner.id,
            "new_post": "new_post",
        }

        # Post the data to create a new post
        response_post = self.client.post(url, data)
        self.assertEqual(response_post.status_code, 302)  # Ensure redirection after successful post creation
        updated_response_get = self.client.get(url, get_data)
        updated_soup = BeautifulSoup(updated_response_get.content, "html.parser")
        new_post = updated_soup.find("a", text="New Post")
        self.assertIsNotNone(new_post, "New post was not created successfully")

    def test_private_community_detail_follower(self):
        self.client.login(username="follower", password="<PASSWORD>")
        url = reverse("community", kwargs={"name": self.private_community.name})
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        community_name = soup.find("h1").text
        self.assertEqual(community_name, self.private_community.name)
        request_btn = soup.find("button", id="request_btn")
        self.assertIn("Send Request", request_btn.text)
        community_posts = soup.find_all("a", id="community-post")
        self.assertIsNotNone(community_posts, None)
        self.client.post(
            url,
            data={"action": {"send_request": True, "request_status": True}},
        )

        response_post = self.client.post(url, data={"action": "send_request"})
        self.assertEqual(response_post.status_code, 200)
        request_exists = CommunityFollowRequests.objects.filter(
            community=self.private_community, user=self.follower
        ).exists()
        self.assertTrue(request_exists)
        response_get_updated = self.client.get(url)
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
        remove_request = self.client.post(url, data={"action": "remove_request"})
        self.assertEqual(remove_request.status_code, 200)
        response_get_updated_btn = self.client.get(url)
        soup_updated_btn = BeautifulSoup(response_get_updated_btn.content, "html.parser")
        updated_request_btn = soup_updated_btn.find("button", id="request_btn")
        self.assertIn("Send Request", updated_request_btn.text)

    def test_public_community_detail_follower(self):
        self.client.login(username="follower", password="<PASSWORD>")
        url = reverse("community", kwargs={"name": self.public_community.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response_follow = self.client.post(url, data={"action": "follow"})
        self.assertEqual(response_follow.status_code, 200)

        response_get_updated = self.client.get(url)
        soup_updated = BeautifulSoup(response_get_updated.content, "html.parser")
        updated_follow_button = soup_updated.find("button", id="follow-button")
        self.assertIn("Unfollow", updated_follow_button.text)

    def test_community_creating(self):
        self.client.login(username="owner", password="<PASSWORD>")
        url = reverse("create_community")
        data = {
            "name": "New Community",
            "description": "Any community detail",
            "is_private": False,
        }
        response_post = self.client.post(url, data)
        self.assertEqual(response_post.status_code, 302)
        response_get = self.client.get(url)
        self.assertIn("form", response_get.context)

        bed_post_response = self.client.post(url)
        self.assertEqual(bed_post_response.status_code, 200)

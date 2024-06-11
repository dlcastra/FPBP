from django.db import models

from users.models import CustomUser


class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500)
    admins = models.ManyToManyField("users.Moderators", related_name="admins")
    posts = models.ManyToManyField("users.Publication", related_name="posts")
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class CommunityFollowers(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="community_relation")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="community_followers")
    is_follow = models.BooleanField(default=True)
    accepted = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.community.name} - {self.user}"

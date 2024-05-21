from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("birthday", date.today())
        extra_fields.setdefault("gender", "P")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    birthday = models.DateField()
    gender = models.CharField(
        max_length=20, choices=(("M", "Male"), ("F", "Female"), ("P", "Preferred not to say")), default="P"
    )
    phone_number = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="photos", null=True, blank=True)
    followers_count = models.IntegerField(default=0)
    followings_count = models.IntegerField(default=0)
    objects = UserManager()

    def __str__(self):
        return self.username


class Followers(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="followers")
    is_follow = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.following}"

from datetime import date

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


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
    birthday = models.DateField(
        default=date.today,
    )
    gender = models.CharField(
        max_length=20,
        choices=(("M", "Male"), ("F", "Female"), ("P", "Preferred not to say")),
        default="P",
    )
    phone_number = PhoneNumberField(blank=True, null=True)
    photo = models.ImageField(upload_to="photos/", null=True, blank=True)
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


class Publication(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, default="")
    author_id = models.PositiveIntegerField(default="", null=False, name="author_id")
    content_object = GenericForeignKey("content_type", "author_id")
    title = models.CharField(max_length=255)
    context = models.TextField()
    attached_image = models.ImageField(upload_to="images/", blank=True)
    attached_file = models.FileField(upload_to="publications/", null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=(
            ("draft", "Draft"),
            ("published", "Published"),
        ),
        default="draft",
    )

    class Meta:
        ordering = ("-published_at",)

    def __str__(self):
        return self.title


class Moderators(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="moderators")
    is_admin = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}"


class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    context = models.TextField()
    attachment = models.FileField(upload_to="attachments", default=None)
    voice = models.FileField(upload_to="voice", default=None)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("date_added",)


class Chat(models.Model):
    chat_name = models.TextField(default="")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sender")
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="recipient")
    message = models.ManyToManyField(Message, related_name="messages")

    def __str__(self):
        return self.chat_name

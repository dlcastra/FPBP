from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from users.models import CustomUser


class Thread(models.Model):
    title = models.CharField(max_length=255)
    context = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="threads")
    published_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="images/", blank=True)
    file = models.FileField(upload_to="files/", blank=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=(
            ("draft", "Draft"),
            ("published", "Published"),
        ),
        default="draft",
    )


class Comments(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_answer")
    title = models.CharField(max_length=255)
    context = models.TextField()
    image = models.ImageField(upload_to="images/answers/", blank=True)
    file = models.FileField(upload_to="files/answers/", blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, default="")
    object_id = models.PositiveIntegerField(default="", null=False)
    content_object = GenericForeignKey("content_type", "object_id")


class ProgrammingLanguage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class TutorialPage(models.Model):
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=200)
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.language.name} - {self.title}"


class SubSection(models.Model):
    page = models.ForeignKey(TutorialPage, on_delete=models.CASCADE, related_name="subsections")
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.page.title} - {self.title}"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=500)

    def __str__(self):
        return self.message

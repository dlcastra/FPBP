from django.db import models
from users.models import CustomUser


class Thread(models.Model):
    title = models.CharField(max_length=255)
    context = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="threads")
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="images/", blank=True)
    file = models.FileField(upload_to="files/", blank=True)


class ThreadAnswer(models.Model):
    id = models.AutoField(primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_answer")
    title = models.CharField(max_length=255)
    context = models.TextField()
    image = models.ImageField(upload_to="images/answers/", blank=True)
    file = models.FileField(upload_to="files/answers/", blank=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="thread_answer")


class ProgrammingLanguage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    template_path = models.CharField(max_length=511, default="/")

    def __str__(self):
        return self.name

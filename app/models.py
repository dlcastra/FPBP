from django.db import models
from users.models import CustomUser


class Thread(models.Model):
    title = models.CharField(max_length=255)
    context = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="threads")
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="images/", blank=True)
    file = models.FileField(upload_to="files/", blank=True)


class ProgrammingLanguage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class TutorialSection(models.Model):
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.language.name} - {self.title}"

# Generated by Django 5.0.6 on 2024-06-09 13:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_rename_user_publication_author_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Moderators",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_admin", models.BooleanField(default=False)),
                ("is_moderator", models.BooleanField(default=False)),
                ("is_owner", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moderators",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

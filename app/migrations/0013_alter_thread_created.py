# Generated by Django 5.0.6 on 2024-06-16 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0012_remove_notification_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="thread",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Upload data from to dp"

    def handle(self, *args, **options): ...

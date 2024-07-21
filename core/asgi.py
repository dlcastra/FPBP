import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import re_path

from app.consumers import NotificationConsumer, CommentsConsumer, ChatConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django_asgi_app = get_asgi_application()
application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        # WebSocket handlers
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    [
                        re_path(r"ws/notify/$", NotificationConsumer.as_asgi()),
                        re_path(r"ws/comments/$", CommentsConsumer.as_asgi()),
                        re_path(r"ws/message/$", ChatConsumer.as_asgi()),
                    ]
                )
            )
        ),
    }
)

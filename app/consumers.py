import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "public_room"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("WebSocket disconnected")

    async def send_notification(self, event):
        message = event["message"]
        safe_message = mark_safe(message)
        await self.send(text_data=json.dumps({"message": safe_message, "id": event["id"]}))

import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from django.utils.safestring import mark_safe

from users.models import Message
from app.models import Comments
from users.models import CustomUser

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


class CommentsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "public_room"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connected")

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):

        data = json.loads(text_data)
        logger.debug(f"Received data: {data}")
        username = data["username"]
        user_id = data.get("user_id")
        content = data.get("content")
        content_type_id = data.get("content_type_id")
        object_ct_id = data.get("object_ct_id")
        object_id = data.get("object_id")
        file = data.get("file")
        image = data.get("image")

        # Ensure all necessary data is present
        if not (content and user_id and content_type_id and object_id):
            logger.error("Missing required fields")
            return

        # Create comment asynchronously using sync_to_async
        comment = await sync_to_async(Comments.objects.create)(
            context=content,
            object_id=object_id,
            image=image,
            file=file,
            user_id=user_id,
            content_type_id=content_type_id,
        )
        logger.info(f"Comment created: {comment.id}")

        response = {
            "type": "send_comment",
            "comment": {
                "username": username,
                "content": comment.context,
                "user_id": comment.user_id,
                "object_id": comment.object_id,
                "object_ct_id": object_ct_id,
            },
        }

        if comment.file:
            response["file_url"] = comment.file.url

        if comment.image:
            response["image_url"] = comment.image.url

        await self.channel_layer.group_send(self.group_name, response)

    async def send_comment(self, event):
        await self.send(
            text_data=json.dumps(
                event,
            )
        )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "public_room"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        logger.info(f"Received data: {data}")

        user_id = data.get("user_id")
        context = data.get("context")
        attachment = data.get("attachment")
        voice = data.get("voice")

        # Ensure username and context are provided
        if not context:
            logger.error("Missing required fields: username or context")
            return

        try:
            user = await sync_to_async(CustomUser.objects.get)(id=user_id)
        except CustomUser.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return

        message = await sync_to_async(Message.objects.create)(
            context=context,
            attachment=attachment,
            voice=voice,
            user=user,
        )
        username = user.username
        response = {
            "type": "send_message",
            "message": {
                "context": message.context,
                "username": username,
                "date": message.date_added.isoformat(),
                "chatId": message.id,
            },
        }

        if message.voice:
            response["voice_url"] = message.voice.url
        if message.attachment:
            response["attachment_url"] = message.attachment.url

        await self.channel_layer.group_send(self.group_name, response)

    async def send_message(self, event):
        await self.send(text_data=json.dumps(event))
        logger.info(f"Sent message: {event}")

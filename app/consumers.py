import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notification_room"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connected to notification group")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("WebSocket disconnected from notification group")

    async def send_notification(self, event):
        message = event["message"]
        safe_message = mark_safe(message)
        await self.send(text_data=json.dumps({"message": safe_message, "id": event["id"]}))


class CommentsConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.group_name = "comments_room"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connected")

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        from app.models import Comments

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
        self.group_name = "chat_room"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("WebSocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected from group: {self.group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        from users.models import Chat, CustomUser
        from app.models import Notification

        data = json.loads(text_data)
        logger.info(f"Received data: {data}")
        chat_id = data.get("chatId")
        recipient = data.get("recipient")
        user_id = data.get("user_id")
        context = data.get("context")
        attachment = data.get("attachment")
        voice = data.get("voice")

        # Ensure context is provided
        if not context:
            logger.error("Missing required fields: context")
            return

        try:
            user = await sync_to_async(CustomUser.objects.get)(id=user_id)
        except CustomUser.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return

        try:
            chat = await sync_to_async(Chat.objects.get)(id=chat_id)
        except Chat.DoesNotExist:
            logger.error(f"Chat {chat_id} not found")
            return

        # Create message related to chat
        message = await sync_to_async(chat.message.create)(
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
                "chatId": chat_id,
            },
        }
        chat_content = await sync_to_async(ContentType.objects.get_for_model)(
            Chat,
        )
        notif, created = await sync_to_async(Notification.objects.get_or_create)(
            user_id=recipient,
            content_type=chat_content,
            object_id=chat.id,
        )
        message_counter = await sync_to_async(chat.message.filter(user_id=recipient).count)()

        if created:
            notif.message = f"You got a new message {message_counter}"
        else:
            notif.message = f"You got a new message {message_counter}"

        await sync_to_async(notif.save)()

        if message.voice:
            response["voice_url"] = message.voice.url
        if message.attachment:
            response["attachment_url"] = message.attachment.url

        await self.channel_layer.group_send(self.group_name, response)
        notification_event = {
            "type": "send_notification",
            "message": notif.message,
            "id": notif.id,
        }
        await self.channel_layer.group_send("notification_room", notification_event)

    async def send_message(self, event):
        await self.send(text_data=json.dumps(event))
        logger.info(f"Sent message: {event}")

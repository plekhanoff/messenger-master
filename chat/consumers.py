import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.chat = await self.get_chat()
        if not self.chat:
            await self.close()
            return

        # Используем безопасное имя группы
        self.room_group_name = self.chat.get_group_name()
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        if not await self.check_user_access():
            await self.close()
            return

        # Подключаемся к группе чата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Загружаем и отправляем историю сообщений
        await self.send_message_history()

    @database_sync_to_async
    def send_message_history(self):
        messages = Message.objects.filter(chat=self.chat).order_by('-timestamp')[:50]
        return [
            {
                'message': message.content,
                'username': message.user.username,
                'timestamp': message.timestamp.strftime("%H:%M")
            }
            for message in messages
        ]

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Сохраняем сообщение
        saved_message = await self.save_message(message)
        
        # Форматируем время
        timestamp = saved_message.timestamp.strftime("%H:%M")

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.user.username,
                'timestamp': timestamp
            }
        )

    async def chat_message(self, event):
        # Отправляем сообщение в WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_chat(self):
        try:
            return Chat.objects.get(name=self.room_name)
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def check_user_access(self):
        return self.user in self.chat.users.all()

    @database_sync_to_async
    def save_message(self, message_content):
        return Message.objects.create(
            chat=self.chat,
            user=self.user,
            content=message_content
        )
   
   

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meds.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are now connected!'
        }))
    
    async def disconnect(self, close_code):
        pass
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            response = {
                'type': 'echo',
                'received': data,
                'status': 'processed'
            }
            await self.send(text_data=json.dumps(response))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'received': text_data,
                'status': 'plain_text'
            }))

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/notifications/", NotificationConsumer.as_asgi()),
        ])
    ),
})
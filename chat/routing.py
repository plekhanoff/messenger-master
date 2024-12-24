from django.urls import re_path
from . import consumers
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', AuthMiddlewareStack(consumers.ChatConsumer.as_asgi())),
]
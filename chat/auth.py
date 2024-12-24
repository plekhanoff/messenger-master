from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()
        
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        token = query_params.get('token', [None])[0]
        scope['user'] = AnonymousUser()
        
        if token:
            try:
                token_obj = await self.get_token(token)
                scope['user'] = token_obj.user
            except Token.DoesNotExist:
                pass
        
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_token(self, token_key):
        return Token.objects.get(key=token_key)

def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner)) 
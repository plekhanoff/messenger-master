from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Chat, Message, UserProfile
from .serializers import ChatSerializer, MessageSerializer, UserProfileSerializer
from django.shortcuts import get_object_or_404

class IsCreatorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action in ['leave_chat', 'add_user', 'remove_user']:
            return request.user in obj.users.all()
        return obj.created_by == request.user

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreatorOrReadOnly]

    def get_queryset(self):
        return Chat.objects.filter(users=self.request.user)

    def perform_create(self, serializer):
        chat = serializer.save(
            created_by=self.request.user,
            is_group=True
        )
        chat.users.add(self.request.user)

    @action(detail=True, methods=['post'])
    def add_user(self, request, pk=None):
        chat = self.get_object()
        user_id = request.data.get('user_id')
        if user_id:
            chat.users.add(user_id)
            return Response({'status': 'user added'})
        return Response({'error': 'user_id required'}, status=400)

    @action(detail=True, methods=['post'])
    def remove_user(self, request, pk=None):
        chat = self.get_object()
        user_id = request.data.get('user_id')
        if user_id:
            chat.users.remove(user_id)
            return Response({'status': 'user removed'})
        return Response({'error': 'user_id required'}, status=400)

    @action(detail=True, methods=['post'])
    def leave_chat(self, request, pk=None):
        chat = self.get_object()
        if chat.is_group and chat.created_by == request.user:
            return Response(
                {'error': 'Создатель не может покинуть групповой чат'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        chat.users.remove(request.user)
        return Response({'status': 'left chat'})

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat_id')
        queryset = Message.objects.filter(chat__users=self.request.user)
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        return queryset

    def perform_create(self, serializer):
        chat_id = self.request.data.get('chat_id')
        chat = get_object_or_404(Chat, id=chat_id)
        if self.request.user not in chat.users.all():
            raise permissions.PermissionDenied("You're not a member of this chat")
        serializer.save(user=self.request.user, chat=chat)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile 
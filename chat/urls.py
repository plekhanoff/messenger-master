from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

router = DefaultRouter()
router.register(r'chats', api_views.ChatViewSet)
router.register(r'messages', api_views.MessageViewSet, basename='message')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.index, name='index'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.user_list, name='user_list'),
    path('create-chat/', views.create_chat, name='create_chat'),
    path('start-chat/<int:user_id>/', views.start_private_chat, name='start_private_chat'),
]

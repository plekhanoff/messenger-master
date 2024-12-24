from rest_framework import serializers
from .models import Chat, Message, UserProfile
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ChatSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Chat
        fields = ['id', 'name', 'users', 'created_at', 'created_by', 'is_group']
        read_only_fields = ['created_at', 'created_by']

    def create(self, validated_data):
        if 'users' not in validated_data:
            validated_data['users'] = []
        return super().create(validated_data)

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Message
        fields = ['id', 'chat', 'user', 'content', 'timestamp']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'avatar']

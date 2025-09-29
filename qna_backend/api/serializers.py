from rest_framework import serializers

from .models import Conversation, Message


class LoginSerializer(serializers.Serializer):
    """Serializer for username/password login and token response."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "messages"]


class AskSerializer(serializers.Serializer):
    """Input payload for submitting a question."""
    question = serializers.CharField()
    conversation_id = serializers.IntegerField(required=False)

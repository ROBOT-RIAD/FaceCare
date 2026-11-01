
from rest_framework import serializers
from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ["id","role","content","created_at",]


class ChatListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    class Meta:
        model = Chat
        fields = ["id","title","last_message","created_at","updated_at",]

    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").first()
        if message:
            return message.content
        return None


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model = Chat
        fields = ["id","title","messages","created_at","updated_at",]


class SendMessageSerializer(serializers.Serializer):

    message = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )

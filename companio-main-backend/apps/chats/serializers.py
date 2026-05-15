from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatSessionListSerializer(serializers.ModelSerializer):
    agent_key = serializers.CharField(source='agent.key', read_only=True)
    agent_display_name = serializers.CharField(source='agent.display_name', read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'agent_key',
            'agent_display_name',
            'title',
            'status',
            'started_at',
            'last_message_at',
            'created_at',
            'updated_at',
        ]


class ChatSessionDetailSerializer(ChatSessionListSerializer):
    pass


class ChatSessionCreateSerializer(serializers.Serializer):
    agent_key = serializers.SlugField(max_length=80, required=False)
    title = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_title(self, value):
        return value.strip()


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'sender',
            'content',
            'status',
            'agent_request_id',
            'safety_status',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000, trim_whitespace=True)

    def validate_content(self, value):
        if not value:
            raise serializers.ValidationError('Message content cannot be empty.')
        return value


class ChatSendResponseSerializer(serializers.Serializer):
    user_message = ChatMessageSerializer()
    agent_message = ChatMessageSerializer()
    usage = serializers.DictField()

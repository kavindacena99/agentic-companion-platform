from rest_framework import serializers


class UsageStatusSerializer(serializers.Serializer):
    date = serializers.DateField()
    messages_used = serializers.IntegerField()
    message_limit = serializers.IntegerField()
    remaining_messages = serializers.IntegerField()
    can_send_message = serializers.BooleanField()

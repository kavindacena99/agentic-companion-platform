from rest_framework import serializers


class AgentAvailabilitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    agent_key = serializers.CharField()
    display_name = serializers.CharField()
    short_description = serializers.CharField(allow_blank=True)
    agent_type = serializers.CharField()
    is_available = serializers.BooleanField()
    availability_status = serializers.CharField()
    requires_premium = serializers.BooleanField()
    runtime_status = serializers.CharField(allow_null=True)
    version = serializers.CharField(allow_null=True)
    supported_features = serializers.ListField(child=serializers.CharField())


class SelectAgentSerializer(serializers.Serializer):
    agent_key = serializers.SlugField(max_length=80)


class SelectedAgentSerializer(serializers.Serializer):
    agent = AgentAvailabilitySerializer(allow_null=True)
    selected_at = serializers.DateTimeField(allow_null=True)

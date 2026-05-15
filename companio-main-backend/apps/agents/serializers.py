from rest_framework import serializers

from .models import Agent, UserAgentSelection


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            'id',
            'key',
            'display_name',
            'short_description',
            'agent_type',
            'is_premium',
            'sort_order',
        ]
        read_only_fields = fields


class SelectAgentSerializer(serializers.Serializer):
    agent_key = serializers.SlugField(max_length=80)


class SelectedAgentSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = UserAgentSelection
        fields = ['agent', 'selected_at']
        read_only_fields = fields

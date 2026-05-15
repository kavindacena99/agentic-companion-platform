from rest_framework import serializers

from .models import SafetyReport


class SafetyReportCreateSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    category = serializers.ChoiceField(choices=SafetyReport.Category.choices)
    description = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )


class SafetyReportSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='message.id', read_only=True)
    session_id = serializers.IntegerField(source='session.id', read_only=True)

    class Meta:
        model = SafetyReport
        fields = [
            'id',
            'session_id',
            'message_id',
            'category',
            'description',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

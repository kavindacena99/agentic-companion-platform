from rest_framework import serializers

from .models import UserProfile
from .services import update_profile_completion


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'email',
            'display_name',
            'birth_date',
            'gender',
            'country',
            'preferred_language',
            'timezone',
            'profile_completed',
            'memory_enabled',
            'personalization_enabled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'profile_completed',
            'created_at',
            'updated_at',
        ]

    def update(self, instance, validated_data):
        profile = super().update(instance, validated_data)
        return update_profile_completion(profile)

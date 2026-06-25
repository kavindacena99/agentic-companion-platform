from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'role',
            'is_active',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'full_name', 'password']

    def validate_email(self, value):
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': UserSerializer(instance).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'full_name']

    def validate_username(self, value):
        qs = User.objects.filter(username=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('This username is already taken.')
        return value


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

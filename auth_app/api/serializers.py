# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework import serializers

# 3. Local
from auth_app.models import UserProfile


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Validates and creates new users with profile.
    """
    fullname = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    repeated_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["email"],
            password=validated_data["password"],
        )
        UserProfile.objects.create(user=user, fullname=validated_data["fullname"])
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Validates email and password credentials.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    Includes user email and fullname.
    """
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["user_id", "email", "fullname"]


class UserCheckSerializer(serializers.Serializer):
    """
    Serializer for checking user by email.
    Returns user info if email exists.
    """
    email = serializers.EmailField(required=True)

# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework import serializers

# 3. Local
from auth_app.models import UserProfile


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration and account creation.
    
    Validates and creates a new user account with associated profile.
    Ensures password confirmation and checks for duplicate email addresses.
    
    Fields:
        fullname (CharField): User's full name (required, max 255 chars)
        email (EmailField): User's email address (required, unique)
        password (CharField): Password for account (required, write-only)
        repeated_password (CharField): Password confirmation (required, write-only)
    
    Validation:
        - Validates that password and repeated_password match
        - Validates that email is unique (no existing user with same email)
        - Email format is validated by EmailField validator
    
    Create Method:
        Creates a new Django User with email as username.
        Creates associated UserProfile with the provided fullname.
        Returns the created User instance.
    
    Used In:
        POST /api/registration/ (user signup endpoint)
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
    Serializer for user login and authentication.
    
    Validates email and password credentials for user authentication.
    Works in conjunction with Django's authenticate() function.
    
    Fields:
        email (EmailField): User's email address (required)
        password (CharField): User's password (required, write-only)
    
    Validation:
        - Email format is validated by EmailField validator
        - Actual credential verification is done in the view (not in serializer)
    
    Note:
        This serializer only validates the input format. The view is responsible
        for calling authenticate() to verify actual credentials.
    
    Used In:
        POST /api/login/ (user login endpoint)
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information retrieval.
    
    Displays essential user profile data including ID, email, and fullname.
    Extracts email from related User model and ID/fullname from UserProfile.
    
    Fields:
        user_id (IntegerField): User's ID from Django User model (read-only, sourced from user.id)
        email (EmailField): User's email from Django User model (read-only, sourced from user.email)
        fullname (CharField): User's full name from UserProfile (read-only)
    
    Model:
        UserProfile
    
    Used In:
        GET /api/email-check/ (returns user info when email is found)
        User responses in other endpoints
    
    Note:
        All fields are read-only as this serializer is used for data retrieval only.
        Sourced fields (email from user.email) use Django's source parameter.
    """
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["user_id", "email", "fullname"]


class UserCheckSerializer(serializers.Serializer):
    """
    Serializer for email existence checking.
    
    Validates and checks if a user with the given email exists.
    Used to verify email availability or find user information.
    
    Fields:
        email (EmailField): Email address to check (required)
    
    Validation:
        - Email format is validated by EmailField validator
        - Actual existence check is performed in the view
    
    Used In:
        GET /api/email-check/?email=user@example.com (check if email is registered)
    
    Note:
        This serializer only validates input format.
        The view handles the actual database lookup.
    """
    email = serializers.EmailField(required=True)

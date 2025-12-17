# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response

# 3. Local
from auth_app.models import UserProfile


def create_token_response(token, user, profile):
    """Build token response with user data."""
    return {
        "token": token.key,
        "user_id": user.id,
        "email": user.email,
        "fullname": profile.fullname,
    }


def get_user_and_profile(email):
    """
    Retrieve user and profile by email.
    
    Returns:
        tuple: (user, profile, error_response) - error_response is None if found
    """
    try:
        user = User.objects.get(email=email)
        profile = UserProfile.objects.get(user=user)
        return user, profile, None
    except User.DoesNotExist:
        return None, None, Response(
            {"error": "Email not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


def authenticate_and_get_token(email, password):
    """
    Authenticate user and return token with profile.
    
    Returns:
        tuple: (token, profile, error_response) - error is None if authenticated
    """
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    from rest_framework import status
    
    user = authenticate(username=email, password=password)
    if not user:
        return None, None, Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    token, _ = Token.objects.get_or_create(user=user)
    profile = UserProfile.objects.get(user=user)
    return token, profile, None

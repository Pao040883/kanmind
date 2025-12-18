# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound, ValidationError

# 3. Local
from auth_app.models import UserProfile


def create_token_response(token, user, profile):
    """Build authentication response dict with token and user info."""
    return {
        "token": token.key,
        "user_id": user.id,
        "email": user.email,
        "fullname": profile.fullname,
    }


def get_user_and_profile(email):
    """
    Fetch user and profile by email.
    
    Returns (user, profile). Raises NotFound if user doesn't exist.
    """
    try:
        user = User.objects.get(email=email)
        profile = UserProfile.objects.get(user=user)
        return user, profile
    except User.DoesNotExist:
        raise NotFound("Email not found")


def authenticate_and_get_token(email, password):
    """
    Authenticate user and return (token, profile).
    
    Raises ValidationError on invalid credentials. Email used as Django auth username.
    """
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    
    user = authenticate(username=email, password=password)
    if not user:
        raise ValidationError({"error": "Invalid credentials"})
    
    token, _ = Token.objects.get_or_create(user=user)
    profile = UserProfile.objects.get(user=user)
    return token, profile
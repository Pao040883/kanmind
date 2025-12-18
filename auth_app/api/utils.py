# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound, ValidationError

# 3. Local
from auth_app.models import UserProfile


def create_token_response(token, user, profile):
    """
    Build authentication response dict with token and user info.
    
    Returns standard format used across login and registration endpoints
    to ensure consistent client-side handling.
    """
    return {
        "token": token.key,
        "user_id": user.id,
        "email": user.email,
        "fullname": profile.fullname,
    }


def get_user_and_profile(email):
    """
    Fetch user and profile by email.
    
    Raises NotFound with "Email not found" message if user doesn't exist.
    Guarantees both User and UserProfile exist on success.
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
    
    Uses email as username for Django authenticate() since user model
    stores email in username field. Creates token if doesn't exist.
    Raises ValidationError with "Invalid credentials" on auth failure.
    """
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    
    user = authenticate(username=email, password=password)
    if not user:
        raise ValidationError({"error": "Invalid credentials"})
    
    token, _ = Token.objects.get_or_create(user=user)
    profile = UserProfile.objects.get(user=user)
    return token, profile
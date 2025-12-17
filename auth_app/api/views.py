# 1. Standard library

# 2. Third-party
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

# 3. Local
from auth_app.api.permissions import IsAuthenticatedUser
from auth_app.api.utils import authenticate_and_get_token, create_token_response, get_user_and_profile
from auth_app.api.serializers import (
    UserCheckSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from auth_app.models import UserProfile


class RegistrationView(APIView):
    """
    User registration and account creation endpoint.
    
    POST /api/registration/
    
    Creates a new user account with an associated profile.
    Returns authentication token and user information upon successful registration.
    
    Request Body (JSON):
        {
            "fullname": "John Doe",
            "email": "john@example.com",
            "password": "securepassword123",
            "repeated_password": "securepassword123"
        }
    
    Success Response (201 Created):
        {
            "token": "abc123...",
            "user_id": 5,
            "email": "john@example.com",
            "fullname": "John Doe"
        }
    
    Error Responses:
        400 Bad Request: Validation errors (mismatched passwords, duplicate email, etc.)
    
    Authentication:
        Disabled (AllowAny) - No authentication required for registration
    
    Validation:
        - Password and repeated_password must match
        - Email must be unique (no existing user with same email)
        - All fields (fullname, email, password, repeated_password) are required
    
    Side Effects:
        - Creates a new Django User with email as username
        - Creates associated UserProfile with the provided fullname
        - Generates an authentication Token for the new user
    
    Permissions:
        AllowAny - Any unauthenticated user can register
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable token auth to avoid 401 when stale token is sent

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            profile = UserProfile.objects.get(user=user)
            response_data = create_token_response(token, user, profile)
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    User login and token authentication endpoint.
    
    POST /api/login/
    
    Authenticates a user and returns an authentication token.
    Uses Django's authenticate() function to verify credentials.
    
    Request Body (JSON):
        {
            "email": "john@example.com",
            "password": "securepassword123"
        }
    
    Success Response (200 OK):
        {
            "token": "abc123...",
            "user_id": 5,
            "email": "john@example.com",
            "fullname": "John Doe"
        }
    
    Error Responses:
        400 Bad Request: Invalid credentials or validation errors
    
    Authentication:
        Disabled (AllowAny) - No authentication required for login
    
    Validation:
        - Email format validation by EmailField
        - Actual credential verification via Django authenticate()
    
    Token Generation:
        - Uses rest_framework.authtoken.Token
        - Gets existing token or creates new one if it doesn't exist
        - Same token returned on subsequent logins
    
    Permissions:
        AllowAny - Any unauthenticated user can login
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable token auth to avoid 401 when stale token is sent

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token, profile = authenticate_and_get_token(
            serializer.validated_data["email"],
            serializer.validated_data["password"]
        )
        
        user = profile.user
        response_data = create_token_response(token, user, profile)
        return Response(response_data, status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """
    Email existence check and user lookup endpoint.
    
    GET /api/email-check/?email=user@example.com
    
    Checks if an email address is registered and returns user information if found.
    Requires authentication to use this endpoint.
    
    Query Parameters:
        email (string, required): Email address to check
    
    Success Response (200 OK) - Email found:
        {
            "user_id": 5,
            "email": "john@example.com",
            "fullname": "John Doe"
        }
    
    Error Responses:
        400 Bad Request: Missing email parameter
        404 Not Found: Email not registered
    
    Authentication:
        Required (IsAuthenticatedUser) - Only authenticated users can check emails
    
    Use Cases:
        - Email availability checking during registration flow
        - User lookup by email
        - Verifying user existence in collaborative features
    
    Permissions:
        IsAuthenticatedUser - Must be logged in
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"error": "Email parameter required"})
        
        user, profile = get_user_and_profile(email)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

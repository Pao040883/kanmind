# 1. Standard library

# 2. Third-party
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# 3. Local
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
    User registration endpoint.
    
    Creates User, UserProfile, and Token in single transaction.
    Disables token auth to prevent 401 when stale tokens are sent.
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
    User login endpoint.
    
    Authenticates via email/password and returns existing or new token.
    Disables token auth to prevent 401 when stale tokens are sent.
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
    Email validation endpoint for adding board members.
    
    Checks if email exists and returns profile data for confirmation.
    Requires authentication to prevent email enumeration attacks.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserCheckSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        user, profile = get_user_and_profile(serializer.validated_data["email"])
        profile_serializer = UserProfileSerializer(profile)
        return Response(profile_serializer.data, status=status.HTTP_200_OK)

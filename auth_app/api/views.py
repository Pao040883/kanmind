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
from auth_app.api.serializers import (
    UserCheckSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from auth_app.models import UserProfile


class RegistrationView(APIView):
    """
    POST: Register a new user.
    Returns token and user information.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable token auth to avoid 401 when stale token is sent

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            profile = UserProfile.objects.get(user=user)
            return Response(
                {
                    "token": token.key,
                    "user_id": user.id,
                    "email": user.email,
                    "fullname": profile.fullname,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST: Authenticate user and return token.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable token auth to avoid 401 when stale token is sent

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                profile = UserProfile.objects.get(user=user)
                return Response(
                    {
                        "token": token.key,
                        "user_id": user.id,
                        "email": user.email,
                        "fullname": profile.fullname,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailCheckView(APIView):
    """
    GET: Check if email exists and return user info.
    Requires authentication.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"error": "Email parameter required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "Email not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

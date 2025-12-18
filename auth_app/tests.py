# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

# 3. Local
from auth_app.models import UserProfile


class RegistrationViewTest(TestCase):
    """Test user registration endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.registration_url = "/api/registration/"

    def test_registration_success(self):
        """Test successful user registration."""
        data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "repeated_password": "testpass123",
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["fullname"], "Test User")

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "repeated_password": "wrongpass",
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_duplicate_email(self):
        """Test registration with existing email."""
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="testpass123",
        )
        data = {
            "fullname": "Test User",
            "email": "existing@example.com",
            "password": "testpass123",
            "repeated_password": "testpass123",
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_missing_fields(self):
        """Test registration with missing required fields."""
        data = {
            "fullname": "Test User",
            "email": "test@example.com",
        }
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 400)


class LoginViewTest(TestCase):
    """Test user login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/login/"
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")

    def test_login_success(self):
        """Test successful login."""
        data = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_login_invalid_password(self):
        """Test login with wrong password."""
        data = {
            "email": "test@example.com",
            "password": "wrongpass",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent email."""
        data = {
            "email": "nonexistent@example.com",
            "password": "testpass123",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_missing_email(self):
        """Test login without email."""
        data = {
            "password": "testpass123",
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)


class EmailCheckViewTest(TestCase):
    """Test email check endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.email_check_url = "/api/email-check/"
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        # Get token for authentication
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)

    def test_email_check_exists(self):
        """Test email check for existing email."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            self.email_check_url, {"email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_email_check_not_exists(self):
        """Test email check for nonexistent email."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            self.email_check_url, {"email": "nonexistent@example.com"}
        )
        self.assertEqual(response.status_code, 404)

    def test_email_check_unauthenticated(self):
        """Test email check without authentication."""
        response = self.client.get(
            self.email_check_url, {"email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 401)

    def test_email_check_missing_email_param(self):
        """Test email check without email parameter."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(self.email_check_url)
        self.assertEqual(response.status_code, 400)

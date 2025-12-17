# 1. Standard library
from datetime import datetime

# 2. Third-party
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Extended user profile model for storing additional user information.
    
    This model extends Django's built-in User model with a OneToOne relationship
    to store application-specific profile data like fullname. It serves as a bridge
    between the Django User model (which contains email and authentication data)
    and application-specific user attributes.
    
    Attributes:
        user (OneToOneField): Links to Django's User model (CASCADE on delete)
        fullname (CharField): The full name of the user (max 255 characters)
        created_at (DateTimeField): Timestamp of profile creation (auto-populated)
        updated_at (DateTimeField): Timestamp of last profile update (auto-updated)
    
    Related Names:
        profile: Accessible from User model as user_instance.profile
    
    Meta:
        Ordered by most recent profile creation date (-created_at).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    fullname = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.fullname} ({self.user.email})"

# 1. Third-party
from rest_framework import permissions


class IsAuthenticatedUser(permissions.BasePermission):
    """Verify user is authenticated."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

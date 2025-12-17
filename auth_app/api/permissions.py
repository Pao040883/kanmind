# 1. Third-party
from rest_framework import permissions


class IsAuthenticatedUser(permissions.BasePermission):
    """
    Allow only authenticated users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

# 1. Third-party
from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """Verify user is authenticated."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsBoardMember(permissions.BasePermission):
    """Allow board owner or members."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.members.all()


class IsBoardOwner(permissions.BasePermission):
    """Allow board owner only."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskBoardMember(permissions.BasePermission):
    """Allow users with access to task's board."""
    def has_object_permission(self, request, view, obj):
        board = obj.board
        return board.owner == request.user or request.user in board.members.all()


class IsTaskCreatorOrBoardOwner(permissions.BasePermission):
    """Allow task creator or board owner."""
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or obj.board.owner == request.user


class IsCommentAuthor(permissions.BasePermission):
    """Allow comment author only."""
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

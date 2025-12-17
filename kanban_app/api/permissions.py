# 1. Third-party
from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """
    Allow only authenticated users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsBoardMember(permissions.BasePermission):
    """
    Allow only board members or owner to access board.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.members.all()


class IsBoardOwner(permissions.BasePermission):
    """
    Allow only board owner to modify board.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskBoardMember(permissions.BasePermission):
    """
    Allow only members of task's board to access task.
    """
    def has_object_permission(self, request, view, obj):
        board = obj.board
        return board.owner == request.user or request.user in board.members.all()


class IsTaskCreatorOrBoardOwner(permissions.BasePermission):
    """
    Allow only task creator or board owner to delete task.
    """
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or obj.board.owner == request.user


class IsCommentAuthor(permissions.BasePermission):
    """
    Allow only comment author to delete comment.
    """
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

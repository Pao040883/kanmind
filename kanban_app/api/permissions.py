# 1. Third-party
from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """
    Custom permission class to verify user is authenticated.
    
    Checks that the request user exists and is authenticated.
    Simpler than DRF's built-in IsAuthenticated but allows for custom extensions.
    
    Method:
        has_permission(request, view) - Checks user authentication status
    
    Returns:
        True if user is authenticated, False otherwise
    
    Raises:
        None - Returns boolean directly
    
    Used In:
        As permission_classes in views that require authentication
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsBoardMember(permissions.BasePermission):
    """
    Object-level permission to check board membership.
    
    Allows access to board data only if the user is either:
    - The board owner, OR
    - A member of the board
    
    Method:
        has_object_permission(request, view, obj) - Checks user's relationship to board
    
    Parameters:
        obj: The Board instance being accessed
    
    Returns:
        True if user is owner or member, False otherwise
    
    Used In:
        Board retrieval and listing
        Task operations within board context
        Any board-level access control
    
    Note:
        Should be used with object-level checking (get_object() in views)
        Works with DRF's filter_queryset() for list views
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.members.all()


class IsBoardOwner(permissions.BasePermission):
    """
    Object-level permission to check board ownership.
    
    Allows access only to the board's owner.
    Stricter than IsBoardMember - members cannot use this permission.
    
    Method:
        has_object_permission(request, view, obj) - Checks if user is owner
    
    Parameters:
        obj: The Board instance being accessed
    
    Returns:
        True if user == obj.owner, False otherwise
    
    Used In:
        Board deletion (only owner can delete)
        Sensitive board operations
        Full board administration
    
    Note:
        Should be used with object-level checking (get_object() in views)
        More restrictive than IsBoardMember permission
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskBoardMember(permissions.BasePermission):
    """
    Object-level permission for task access within a board.
    
    Allows access to a task only if the user is a member of the task's board.
    Checks both board owner and board members.
    
    Method:
        has_object_permission(request, view, obj) - Checks task's board membership
    
    Parameters:
        obj: The Task instance being accessed
    
    Logic:
        1. Get the task's board via obj.board
        2. Check if user == board.owner OR user in board.members.all()
    
    Returns:
        True if user is board member/owner, False otherwise
    
    Used In:
        Task retrieval
        Task listing within board
        Task modification permission checks
    
    Note:
        Permissions are transitive - if you can access the board, you can access its tasks
        Tasks belong to boards, so board membership is the relevant check
    """
    def has_object_permission(self, request, view, obj):
        board = obj.board
        return board.owner == request.user or request.user in board.members.all()


class IsTaskCreatorOrBoardOwner(permissions.BasePermission):
    """
    Object-level permission for sensitive task operations.
    
    Allows operation only if user is the task creator OR the board owner.
    Used for task deletion to ensure proper control.
    
    Method:
        has_object_permission(request, view, obj) - Checks task creator or board ownership
    
    Parameters:
        obj: The Task instance being accessed
    
    Returns:
        True if user == obj.created_by OR user == obj.board.owner, False otherwise
    
    Rationale:
        - Task creator should always be able to delete their own task
        - Board owner should be able to delete any task in their board
        - Regular board members cannot delete others' tasks
    
    Used In:
        Task deletion (DELETE /api/tasks/{id}/)
        Major task modifications
    
    Note:
        More restrictive than IsBoardMember
        Prevents members from deleting other members' tasks
    """
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or obj.board.owner == request.user


class IsCommentAuthor(permissions.BasePermission):
    """
    Object-level permission for comment author verification.
    
    Allows operation only if the user is the original comment author.
    Used to prevent users from modifying or deleting other users' comments.
    
    Method:
        has_object_permission(request, view, obj) - Checks comment authorship
    
    Parameters:
        obj: The Comment instance being accessed
    
    Returns:
        True if user == obj.author, False otherwise
    
    Used In:
        Comment deletion (DELETE /api/tasks/{task_id}/comments/{comment_id}/)
        Comment modification (if implemented)
    
    Note:
        Strict permission - only the exact author can modify/delete
        Board owner does NOT have override permission for comments
        Ensures user privacy in discussions
    """
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

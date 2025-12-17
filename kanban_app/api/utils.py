# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response

# 3. Local
from kanban_app.models import Board, Task


def validate_board_membership(board, user):
    """Check if user is board member or owner."""
    return user in board.members.all() or board.owner == user


def validate_and_get_assignee(assignee_id, board):
    """
    Validate and retrieve assignee user.
    
    Returns:
        tuple: (assignee_user, error_response) - error_response is None if valid
    """
    if not assignee_id:
        return None, None
    
    try:
        assignee = User.objects.get(id=assignee_id)
        if assignee not in board.members.all():
            return None, Response(
                {"error": "Assignee not in board members"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return assignee, None
    except User.DoesNotExist:
        return None, Response(
            {"error": "Assignee not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def validate_and_get_reviewer(reviewer_id, board):
    """
    Validate and retrieve reviewer user.
    
    Returns:
        tuple: (reviewer_user, error_response) - error_response is None if valid
    """
    if not reviewer_id:
        return None, None
    
    try:
        reviewer = User.objects.get(id=reviewer_id)
        if reviewer not in board.members.all():
            return None, Response(
                {"error": "Reviewer not in board members"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return reviewer, None
    except User.DoesNotExist:
        return None, Response(
            {"error": "Reviewer not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def create_task_from_data(board, validated_data, assignee, reviewer, created_by):
    """Create task instance with provided data."""
    return Task.objects.create(
        board=board,
        title=validated_data["title"],
        description=validated_data.get("description"),
        status=validated_data.get("status", "to-do"),
        priority=validated_data.get("priority", "medium"),
        assignee=assignee,
        reviewer=reviewer,
        due_date=validated_data.get("due_date"),
        created_by=created_by,
    )


def update_task_fields(task, validated_data):
    """Update task fields from validated data."""
    task.title = validated_data.get("title", task.title)
    task.description = validated_data.get("description", task.description)
    task.status = validated_data.get("status", task.status)
    task.priority = validated_data.get("priority", task.priority)
    task.due_date = validated_data.get("due_date", task.due_date)
    task.save()


def get_board_or_error(board_id):
    """
    Get board by ID or return error response.
    
    Returns:
        tuple: (board, error_response) - error_response is None if found
    """
    try:
        board = Board.objects.get(id=board_id)
        return board, None
    except Board.DoesNotExist:
        return None, Response(
            {"error": "Board not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


def validate_task_assignees(request_data, board):
    """
    Validate and set assignee and reviewer from request data.
    
    Returns:
        tuple: (assignee, reviewer, error_response) - error is None if all valid
    """
    assignee, error = validate_and_get_assignee(request_data.get("assignee_id"), board)
    if error:
        return None, None, error
    
    reviewer, error = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
    if error:
        return None, None, error
    
    return assignee, reviewer, None


def update_task_assignee_if_provided(task, request_data, board):
    """Update task assignee if assignee_id is in request data."""
    if "assignee_id" in request_data:
        assignee, error = validate_and_get_assignee(request_data.get("assignee_id"), board)
        if error:
            return error
        task.assignee = assignee
    return None


def update_task_reviewer_if_provided(task, request_data, board):
    """Update task reviewer if reviewer_id is in request data."""
    if "reviewer_id" in request_data:
        reviewer, error = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
        if error:
            return error
        task.reviewer = reviewer
    return None


def validate_serializer_and_respond(serializer):
    """
    Validate serializer and return error response if invalid.
    
    Returns:
        Response or None - Returns error response if invalid, None if valid
    """
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return None


def check_board_permission(board, user):
    """
    Check board membership and return error if denied.
    
    Returns:
        Response or None - Returns error response if denied, None if allowed
    """
    if not validate_board_membership(board, user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    return None


def process_task_creation(board, validated_data, request_data, user):
    """Process task creation with assignee/reviewer validation."""
    assignee, reviewer, error = validate_task_assignees(request_data, board)
    if error:
        return None, error
    
    task = create_task_from_data(board, validated_data, assignee, reviewer, user)
    return task, None


def update_task_assignees(task, request_data):
    """Update task assignee and reviewer if provided in request."""
    error = update_task_assignee_if_provided(task, request_data, task.board)
    if error:
        return error
    
    error = update_task_reviewer_if_provided(task, request_data, task.board)
    if error:
        return error
    
    return None

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
    Validate assignee exists and is board member. Return (assignee, error).
    
    Allows optional assignment (returns None, None if assignee_id not provided).
    HTTP 400 if validation fails.
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
    Validate reviewer exists and is board member. Return (reviewer, error).
    
    Allows optional assignment (returns None, None if reviewer_id not provided).
    HTTP 400 if validation fails.
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
    """Create and persist Task instance with provided data and user references."""
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
    """Update Task fields from validated data and persist to database."""
    task.title = validated_data.get("title", task.title)
    task.description = validated_data.get("description", task.description)
    task.status = validated_data.get("status", task.status)
    task.priority = validated_data.get("priority", task.priority)
    task.due_date = validated_data.get("due_date", task.due_date)
    task.save()


def get_board_or_error(board_id):
    """Fetch Board by ID or return HTTP 404 error response tuple."""
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
    Validate both assignee and reviewer from request data. Return (assignee, reviewer, error).
    \n    HTTP 400 if any validation fails.
    """
    assignee, error = validate_and_get_assignee(request_data.get("assignee_id"), board)
    if error:
        return None, None, error
    
    reviewer, error = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
    if error:
        return None, None, error
    
    return assignee, reviewer, None


def update_task_assignee_if_provided(task, request_data, board):
    """Update task.assignee if 'assignee_id' in request_data. Return error or None."""
    if "assignee_id" in request_data:
        assignee, error = validate_and_get_assignee(request_data.get("assignee_id"), board)
        if error:
            return error
        task.assignee = assignee
    return None


def update_task_reviewer_if_provided(task, request_data, board):
    """Update task.reviewer if 'reviewer_id' in request_data. Return error or None."""
    if "reviewer_id" in request_data:
        reviewer, error = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
        if error:
            return error
        task.reviewer = reviewer
    return None


def validate_serializer_and_respond(serializer):
    """Return HTTP 400 response if serializer invalid, else None."""
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return None


def check_board_permission(board, user):
    """Return HTTP 403 response if user lacks board access, else None."""
    if not validate_board_membership(board, user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    return None


def process_task_creation(board, validated_data, request_data, user):
    """
    Validate and create Task with assignee/reviewer. Return (task, error).
    
    Encapsulates full task creation logic for concise view methods.
    """
    assignee, reviewer, error = validate_task_assignees(request_data, board)
    if error:
        return None, error
    
    task = create_task_from_data(board, validated_data, assignee, reviewer, user)
    return task, None


def update_task_assignees(task, request_data):
    """
    Update task.assignee and task.reviewer if provided. Return error or None.
    
    Does NOT save task - caller must save. Short-circuits on first error.
    """
    error = update_task_assignee_if_provided(task, request_data, task.board)
    if error:
        return error
    
    error = update_task_reviewer_if_provided(task, request_data, task.board)
    if error:
        return error
    
    return None

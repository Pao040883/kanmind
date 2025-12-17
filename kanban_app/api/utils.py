# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

# 3. Local
from kanban_app.models import Board, Task


def validate_board_membership(board, user):
    """Check if user is board member or owner."""
    return user in board.members.all() or board.owner == user


def validate_and_get_assignee(assignee_id, board):
    """
    Validate assignee exists and is board member. Return assignee or None.
    
    Allows optional assignment (returns None if assignee_id not provided).
    Raises ValidationError if validation fails.
    """
    if not assignee_id:
        return None
    
    try:
        assignee = User.objects.get(id=assignee_id)
        if assignee not in board.members.all():
            raise ValidationError({"error": "Assignee not in board members"})
        return assignee
    except User.DoesNotExist:
        raise ValidationError({"error": "Assignee not found"})


def validate_and_get_reviewer(reviewer_id, board):
    """
    Validate reviewer exists and is board member. Return reviewer or None.
    
    Allows optional assignment (returns None if reviewer_id not provided).
    Raises ValidationError if validation fails.
    """
    if not reviewer_id:
        return None
    
    try:
        reviewer = User.objects.get(id=reviewer_id)
        if reviewer not in board.members.all():
            raise ValidationError({"error": "Reviewer not in board members"})
        return reviewer
    except User.DoesNotExist:
        raise ValidationError({"error": "Reviewer not found"})


def create_task_from_data(board, validated_data, assignee, reviewer, created_by):
    """Create and return Task instance from validated data and relationships."""
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
    """Fetch Board by ID. Raises NotFound if board doesn't exist."""
    try:
        return Board.objects.get(id=board_id)
    except Board.DoesNotExist:
        raise NotFound("Board not found")


def validate_task_assignees(request_data, board):
    """
    Validate both assignee and reviewer from request data. Return (assignee, reviewer).
    
    Raises ValidationError if any validation fails.
    """
    assignee = validate_and_get_assignee(request_data.get("assignee_id"), board)
    reviewer = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
    return assignee, reviewer


def update_task_assignee_if_provided(task, request_data, board):
    """Update task.assignee if 'assignee_id' in request_data. Raises ValidationError on failure."""
    if "assignee_id" in request_data:
        assignee = validate_and_get_assignee(request_data.get("assignee_id"), board)
        task.assignee = assignee


def update_task_reviewer_if_provided(task, request_data, board):
    """Update task.reviewer if 'reviewer_id' in request_data. Raises ValidationError on failure."""
    if "reviewer_id" in request_data:
        reviewer = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
        task.reviewer = reviewer


def validate_serializer(serializer):
    """Validate serializer. Raises ValidationError if invalid."""
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)


def check_board_permission(board, user, require_owner_or_creator=None):
    """
    Check if user has board access. Raises PermissionDenied if not.
    
    If require_owner_or_creator is provided (a User), requires user to be either
    board owner OR the creator.
    """
    if require_owner_or_creator:
        if user != board.owner and user != require_owner_or_creator:
            raise PermissionDenied("Permission denied")
    elif not validate_board_membership(board, user):
        raise PermissionDenied("Permission denied")


def process_task_creation(board, validated_data, request_data, user):
    """
    Validate and create Task with assignee/reviewer. Return task.
    
    Raises ValidationError if validation fails.
    """
    assignee, reviewer = validate_task_assignees(request_data, board)
    return create_task_from_data(board, validated_data, assignee, reviewer, user)


def update_task_assignees(task, request_data):
    """
    Update task.assignee and task.reviewer if provided.
    
    Does NOT save task - caller must save. Raises ValidationError on failure.
    """
    update_task_assignee_if_provided(task, request_data, task.board)
    update_task_reviewer_if_provided(task, request_data, task.board)

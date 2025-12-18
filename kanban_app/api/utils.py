# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

# 3. Local
from kanban_app.models import Board, Task


def validate_board_membership(board, user):
    """
    Check if user has access to board.
    
    Returns True if user is board owner OR in members list.
    Used for read/update operations where both owners and members have access.
    """
    return user in board.members.all() or board.owner == user


def validate_and_get_assignee(assignee_id, board):
    """
    Validate assignee exists and is board member.
    
    Returns None if assignee_id not provided (allows optional assignment).
    Raises ValidationError if assignee doesn't exist or isn't board member.
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
    Validate reviewer exists and is board member.
    
    Returns None if reviewer_id not provided (allows optional assignment).
    Raises ValidationError if reviewer doesn't exist or isn't board member.
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
    """
    Create and return Task instance from validated data and relationships.
    
    Sets default values for status (to-do) and priority (medium) if not provided.
    Tracks created_by for deletion permission checks.
    """
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
    """
    Update Task fields from validated data and persist to database.
    
    Uses get() with current value fallback to preserve unchanged fields.
    Handles all standard task fields except assignee/reviewer (separate logic).
    """
    task.title = validated_data.get("title", task.title)
    task.description = validated_data.get("description", task.description)
    task.status = validated_data.get("status", task.status)
    task.priority = validated_data.get("priority", task.priority)
    task.due_date = validated_data.get("due_date", task.due_date)
    task.save()


def get_board_or_error(board_id):
    """
    Fetch Board by ID.
    
    Raises NotFound with "Board not found" message if board doesn't exist.
    Used for task creation to validate board_id before proceeding.
    """
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
    """
    Update task.assignee if 'assignee_id' in request_data.
    
    Checks for key existence (not just value) to allow setting assignee to None.
    Validates assignee is board member. Raises ValidationError on failure.
    """
    if "assignee_id" in request_data:
        assignee = validate_and_get_assignee(request_data.get("assignee_id"), board)
        task.assignee = assignee


def update_task_reviewer_if_provided(task, request_data, board):
    """
    Update task.reviewer if 'reviewer_id' in request_data.
    
    Checks for key existence (not just value) to allow setting reviewer to None.
    Validates reviewer is board member. Raises ValidationError on failure.
    """
    if "reviewer_id" in request_data:
        reviewer = validate_and_get_reviewer(request_data.get("reviewer_id"), board)
        task.reviewer = reviewer


def validate_serializer(serializer):
    """
    Validate serializer and raise exception on failure.
    
    Centralizes validation logic to avoid repeating is_valid() checks.
    Automatically includes serializer.errors in ValidationError.
    """
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)


def check_board_permission(board, user, require_owner_or_creator=None):
    """
    Check board access permission.
    
    If require_owner_or_creator is provided, requires user to be either
    board owner OR the specified creator (used for task deletion).
    """
    if require_owner_or_creator:
        if user != board.owner and user != require_owner_or_creator:
            raise PermissionDenied("Permission denied")
    elif not validate_board_membership(board, user):
        raise PermissionDenied("Permission denied")


def process_task_creation(board, validated_data, request_data, user):
    """
    Validate and create Task with assignee/reviewer.
    
    Validates both assignee and reviewer are board members before creation.
    Combines validation and creation in single transaction.
    """
    assignee, reviewer = validate_task_assignees(request_data, board)
    return create_task_from_data(board, validated_data, assignee, reviewer, user)


def update_task_assignees(task, request_data):
    """
    Update task assignee/reviewer if provided.
    
    Does NOT save task - caller is responsible for saving.
    Allows batching assignee/reviewer updates with field updates.
    """
    update_task_assignee_if_provided(task, request_data, task.board)
    update_task_reviewer_if_provided(task, request_data, task.board)

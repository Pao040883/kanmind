# 1. Third-party
from rest_framework import serializers

# 2. Local
from auth_app.models import UserProfile
from django.contrib.auth.models import User
from kanban_app.models import Board, Comment, Task


class UserSimpleSerializer(serializers.Serializer):
    """
    Lightweight serializer for user information in nested responses.
    
    Used to display user details in nested contexts (e.g., within board/task responses)
    without exposing sensitive information or unnecessary data.
    
    Fields:
        id (IntegerField): User's ID
        email (EmailField): User's email address
        fullname (CharField): User's full name (extracted from UserProfile)
    
    Data Sources:
        - id: Django User.id
        - email: Django User.email
        - fullname: UserProfile.fullname (gracefully falls back to User.username if profile missing)
    
    Fallback Behavior:
        If UserProfile is not found, uses User.username as fullname (fallback).
    
    Used In:
        Nested in BoardDetailSerializer (members list)
        Nested in TaskSerializer (assignee, reviewer fields)
        Nested in BoardUpdateSerializer (members_data)
    
    Note:
        This is a lightweight alternative to full UserProfileSerializer.
        Used to keep response payloads smaller in nested structures.
    """
    id = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    fullname = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.id

    def get_email(self, obj):
        return obj.email

    def get_fullname(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.fullname if profile else obj.username


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for board list view with statistics.
    
    Displays a summary of boards with key metrics and counts.
    Used when listing all boards the user is a member of or owns.
    
    Fields:
        id (IntegerField): Board ID (read-only)
        title (CharField): Board title/name (read-only)
        member_count (SerializerMethodField): Number of board members
        ticket_count (SerializerMethodField): Total number of tasks
        tasks_to_do_count (SerializerMethodField): Number of tasks with status "to-do"
        tasks_high_prio_count (SerializerMethodField): Number of high-priority tasks
        owner_id (IntegerField): ID of the board owner (sourced from owner.id)
    
    Computed Fields (SerializerMethodField):
        - member_count: Count of board members (board.members.count())
        - ticket_count: Total task count (board.tasks.count())
        - tasks_to_do_count: Tasks in "to-do" status
        - tasks_high_prio_count: Tasks with "high" priority
    
    Model:
        Board
    
    Used In:
        GET /api/boards/ (list user's boards)
        POST /api/boards/ (create response includes list serializer format)
    
    Note:
        Provides quick overview statistics without loading full task details.
        Optimized for list views where full task data is not needed.
    """
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments with author information.
    
    Displays comment details including the author's full name, content, and creation timestamp.
    Ordered chronologically to show comment threads in sequence.
    
    Fields:
        id (IntegerField): Comment ID (read-only)
        created_at (DateTimeField): Timestamp when comment was created (read-only)
        author (CharField): Author's full name (read-only, sourced from author.userprofile.fullname)
        content (TextField): Comment text content (read-write)
    
    Model:
        Comment
    
    Data Sources:
        - author field uses source="author.userprofile.fullname" to extract the full name
    
    Used In:
        GET /api/tasks/{id}/comments/ (list comments on a task)
        POST /api/tasks/{id}/comments/ (create/response)
        Nested in task responses
    
    Note:
        Comments are ordered by created_at (earliest first) in the default ordering.
        The author field is read-only and extracted from the related User/UserProfile.
    """
    author = serializers.CharField(source="author.userprofile.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task detail view with full information.
    
    Provides complete task data including nested user information, comments count,
    and supports both read and write operations with validation.
    
    Fields:
        id (IntegerField): Task ID (read-only)
        board (IntegerField): Board ID (read-only, cannot be changed)
        title (CharField): Task title (required, read-write)
        description (TextField): Task description (optional, read-write)
        status (CharField): Task status from choices (read-write)
        priority (CharField): Task priority from choices (read-write)
        assignee (UserSimpleSerializer): Assigned user info (read-only, nested)
        assignee_id (IntegerField): ID of assigned user (write-only, for setting assignee)
        reviewer (UserSimpleSerializer): Reviewer user info (read-only, nested)
        reviewer_id (IntegerField): ID of reviewer (write-only, for setting reviewer)
        due_date (DateField): Task deadline (optional, read-write)
        comments_count (SerializerMethodField): Number of comments on task
    
    Validation:
        status: Must be one of "to-do", "in-progress", "review", "done"
        priority: Must be one of "low", "medium", "high"
    
    Model:
        Task
    
    Used In:
        GET /api/tasks/{id}/ (retrieve single task)
        PATCH /api/tasks/{id}/ (update task)
        POST /api/tasks/ (create task)
    
    Note:
        Assignee/Reviewer fields use separate write-only ID fields (assignee_id, reviewer_id)
        for creation/updates while displaying full user info on read.
        Board field is read-only to prevent moving tasks between boards.
    """
    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]
        read_only_fields = ["board"]

    def get_comments_count(self, obj):
        return obj.comments.count()

    def validate_status(self, value):
        valid_statuses = ["to-do", "in-progress", "review", "done"]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of {valid_statuses}")
        return value

    def validate_priority(self, value):
        valid_priorities = ["low", "medium", "high"]
        if value not in valid_priorities:
            raise serializers.ValidationError(f"Priority must be one of {valid_priorities}")
        return value


class TaskNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for tasks within board detail responses.
    
    Lightweight version of TaskSerializer used when tasks are nested inside board details.
    Excludes the board field to avoid redundant circular references.
    
    Fields:
        id (IntegerField): Task ID (read-only)
        title (CharField): Task title (read-only)
        description (TextField): Task description (read-only)
        status (CharField): Task status (read-only)
        priority (CharField): Task priority (read-only)
        assignee (UserSimpleSerializer): Assigned user info (read-only, nested)
        reviewer (UserSimpleSerializer): Reviewer user info (read-only, nested)
        due_date (DateField): Task deadline (read-only)
        comments_count (SerializerMethodField): Number of comments on task
    
    Model:
        Task
    
    Differences from TaskSerializer:
        - Excludes board field (implicit from parent board)
        - All fields read-only (not used for creation/updates)
        - Uses UserSimpleSerializer for nested user data
    
    Used In:
        Nested in BoardDetailSerializer (tasks list within board detail)
    
    Note:
        This is a read-only view designed specifically for board detail responses
        where the board context is already clear.
    """
    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for board detail view with full board information.
    
    Provides comprehensive board data including all members and all tasks
    with their full details. Used for the board detail endpoint.
    
    Fields:
        id (IntegerField): Board ID (read-only)
        title (CharField): Board title/name (read-only)
        owner_id (IntegerField): ID of board owner (read-only, sourced from owner.id)
        members (UserSimpleSerializer): List of board members (read-only, nested, many=True)
        tasks (TaskNestedSerializer): List of board tasks (read-only, nested, many=True)
    
    Model:
        Board
    
    Nested Serializers:
        members: Uses UserSimpleSerializer for each member
        tasks: Uses TaskNestedSerializer (without board field to avoid redundancy)
    
    Used In:
        GET /api/boards/{id}/ (retrieve single board with all details)
    
    Note:
        Provides complete board context with all members and tasks.
        Tasks use TaskNestedSerializer which excludes board field (redundant).
        This is a read-only view for data retrieval only.
    """
    members = UserSimpleSerializer(many=True, read_only=True)
    tasks = TaskNestedSerializer(many=True, read_only=True)
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating board information.
    
    Used when updating board details (title, members). Separates read and write
    operations for members using different field names.
    
    Fields:
        id (IntegerField): Board ID (read-only)
        title (CharField): Board title (read-write, can update)
        owner_data (UserSimpleSerializer): Owner information (read-only, nested)
        members (PrimaryKeyRelatedField): Member IDs for update (write-only, many=True)
        members_data (UserSimpleSerializer): Member information (read-only, nested)
    
    Model:
        Board
    
    Field Details:
        members: Takes list of User IDs for writing/updating (write_only=True)
        members_data: Returns full member details after update (sourced from members, read_only=True)
        owner_data: Returns owner details (sourced from owner, read_only=True)
    
    Used In:
        PATCH /api/boards/{id}/ (update board title and/or members)
    
    Update Behavior:
        Updates board.title if provided
        Replaces board.members if provided (uses set() to replace entire membership)
    
    Note:
        Uses separate field names (members for write, members_data for read) to handle
        different formats: write receives IDs, read returns full user objects.
    """
    members_data = UserSimpleSerializer(source="members", many=True, read_only=True)
    owner_data = UserSimpleSerializer(source="owner", read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False, write_only=True
    )

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members", "members_data"]

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        if "members" in validated_data:
            instance.members.set(validated_data["members"])
        instance.save()
        return instance


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new board.
    
    Used when creating a board. The current user automatically becomes the owner.
    Optionally accepts initial members list.
    
    Fields:
        title (CharField): Board title/name (required)
        members (PrimaryKeyRelatedField): User IDs to add as initial members (optional, many=True)
    
    Model:
        Board
    
    Create Behavior:
        Owner is automatically set to the current authenticated user (passed from view).
        Members are set from the provided list.
    
    Used In:
        POST /api/boards/ (create a new board)
    
    Note:
        Does not include owner field - it's automatically set via serializer.save(owner=user).
        Members are optional for initial creation; can be added later.
    """
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )

    class Meta:
        model = Board
        fields = ["title", "members"]
    
    def create(self, validated_data):
        members = validated_data.pop('members', [])
        board = Board.objects.create(**validated_data)
        board.members.set(members)
        return board

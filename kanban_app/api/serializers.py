# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from django.db import models
from rest_framework import serializers

# 3. Local
from auth_app.models import UserProfile
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
        - author field uses source="author.profile.fullname" to extract the full name
    
    Used In:
        GET /api/tasks/{id}/comments/ (list comments on a task)
        POST /api/tasks/{id}/comments/ (create/response)
        Nested in task responses
    
    Note:
        Comments are ordered by created_at (earliest first) in the default ordering.
        The author field is read-only and extracted from the related User/UserProfile.
    """
    author = serializers.CharField(source="author.profile.fullname", read_only=True)

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
        board (IntegerField): Board ID (read-only, cannot be changed after creation)
        title (CharField): Task title (required, read-write)
        description (TextField): Task description (optional, read-write)
        status (CharField): Task status - must be one of: "to-do", "in-progress", "review", "done" (read-write)
        priority (CharField): Task priority - must be one of: "low", "medium", "high" (read-write)
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


class BoardUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating board information.
    
    Uses Serializer (not ModelSerializer) to avoid conflicts with ManyToMany field handling.
    Manually handles all fields to match endpoints.md specification.
    
    Fields:
        id (IntegerField): Board ID (read-only)
        title (CharField): Board title (read-write, can update)
        owner_data (dict): Owner information (read-only, nested)
        members (list): Member IDs for update (write-only)
        members_data (list): Member information (read-only, nested)
    
    Used In:
        PATCH /api/boards/{id}/ (update board title and/or members)
    
    Update Behavior:
        Updates board.title if provided
        Replaces board.members if provided (uses set() to replace entire membership)
    
    Note:
        Not using ModelSerializer to avoid ManyToMany field conflicts.
    """
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=False, max_length=255)
    owner_data = serializers.SerializerMethodField()
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    members_data = serializers.SerializerMethodField()

    def get_owner_data(self, obj):
        return {
            'id': obj.owner.id,
            'email': obj.owner.email,
            'fullname': obj.owner.profile.fullname if hasattr(obj.owner, 'profile') else obj.owner.username
        }
    
    def get_members_data(self, obj):
        members_list = []
        for member in obj.members.all():
            members_list.append({
                'id': member.id,
                'email': member.email,
                'fullname': member.profile.fullname if hasattr(member, 'profile') else member.username
            })
        return members_list

    def validate_members(self, value):
        """
        Validate that members being removed are not assigned to any tasks.
        
        Prevents removing board members who are still assigned as assignee or reviewer
        on active tasks to maintain data consistency.
        """
        if not self.instance:
            return value
        
        # Get current members
        current_member_ids = set(self.instance.members.values_list('id', flat=True))
        # Get new members
        new_member_ids = set(value)
        # Find members being removed
        removed_member_ids = current_member_ids - new_member_ids
        
        if removed_member_ids:
            # Check if any removed members are assigned to tasks
            tasks_with_removed_members = self.instance.tasks.filter(
                models.Q(assignee_id__in=removed_member_ids) | 
                models.Q(reviewer_id__in=removed_member_ids)
            )
            
            if tasks_with_removed_members.exists():
                # Get names of affected users for error message
                from django.contrib.auth.models import User
                affected_users = User.objects.filter(id__in=removed_member_ids)
                user_names = [u.email for u in affected_users]
                
                raise serializers.ValidationError(
                    f"Cannot remove members {', '.join(user_names)} because they are still assigned to tasks. "
                    "Please reassign or remove their tasks first."
                )
        
        return value

    def update(self, instance, validated_data):
        # Update title if provided
        if "title" in validated_data:
            instance.title = validated_data["title"]
            instance.save()
        
        # Update members if provided
        if "members" in validated_data:
            member_ids = validated_data["members"]
            users = User.objects.filter(id__in=member_ids)
            instance.members.set(users)
        
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


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for task PATCH responses.
    
    According to endpoints.md, PATCH /api/tasks/{id}/ should NOT include board field.
    This is different from POST /api/tasks/ and GET responses which include board.
    
    Fields:
        id (IntegerField): Task ID (read-only)
        title (CharField): Task title (read-only in response)
        description (TextField): Task description (read-only in response)
        status (CharField): Task status (read-only in response)
        priority (CharField): Task priority (read-only in response)
        assignee (UserSimpleSerializer): Assigned user info (read-only, nested)
        reviewer (UserSimpleSerializer): Reviewer user info (read-only, nested)
        due_date (DateField): Task deadline (read-only in response)
    
    Model:
        Task
    
    Used In:
        PATCH /api/tasks/{id}/ response only
    
    Note:
        Excludes board field to match endpoints.md specification.
        Excludes comments_count since not in spec.
    """
    assignee = UserSimpleSerializer(read_only=True)
    reviewer = UserSimpleSerializer(read_only=True)

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
        ]

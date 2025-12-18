# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from django.db import models
from rest_framework import serializers

# 3. Local
from auth_app.models import UserProfile
from kanban_app.models import Board, Comment, Task


class NestedUserSerializer(serializers.Serializer):
    """
    User serializer for nested contexts (assignee, reviewer, members).
    
    Uses SerializerMethodField for fullname with profile fallback.
    Returns username if UserProfile doesn't exist.
    """
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    fullname = serializers.SerializerMethodField()

    def get_fullname(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.fullname if profile else obj.username


class BoardListSerializer(serializers.ModelSerializer):
    """
    Board overview with computed statistics.
    
    Calculates member count, total tasks, tasks in to-do status, and high-priority tasks.
    Optimized for list views without loading full task details.
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
    author = serializers.CharField(source="author.profile.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]


class TaskSerializer(serializers.ModelSerializer):
    """
    Full task serializer with nested user data and validation.
    
    Uses separate write-only ID fields (assignee_id, reviewer_id) for updates
    while displaying full nested user info on read.
    """
    assignee = NestedUserSerializer(read_only=True)
    reviewer = NestedUserSerializer(read_only=True)
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
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of {valid_statuses}")
        return value

    def validate_priority(self, value):
        valid_priorities = [choice[0] for choice in Task.PRIORITY_CHOICES]
        if value not in valid_priorities:
            raise serializers.ValidationError(f"Priority must be one of {valid_priorities}")
        return value


class TaskNestedSerializer(serializers.ModelSerializer):
    """Excludes board field to avoid redundancy when nested in BoardDetail."""
    assignee = NestedUserSerializer(read_only=True)
    reviewer = NestedUserSerializer(read_only=True)
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
    members = NestedUserSerializer(many=True, read_only=True)
    tasks = TaskNestedSerializer(many=True, read_only=True)
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.Serializer):
    """
    Board update with member validation.
    
    Uses Serializer (not ModelSerializer) to avoid ManyToMany field conflicts.
    Validates that members being removed are not assigned to tasks.
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

    def _serialize_user(self, user):
        """Helper method to serialize user data with profile fallback."""
        return {
            'id': user.id,
            'email': user.email,
            'fullname': user.profile.fullname if hasattr(user, 'profile') else user.username
        }

    def get_owner_data(self, obj):
        return self._serialize_user(obj.owner)
    
    def get_members_data(self, obj):
        return [self._serialize_user(member) for member in obj.members.all()]

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
    assignee = NestedUserSerializer(read_only=True)
    reviewer = NestedUserSerializer(read_only=True)

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

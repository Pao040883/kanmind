# 1. Third-party
from rest_framework import serializers

# 2. Local
from auth_app.models import UserProfile
from django.contrib.auth.models import User
from kanban_app.models import Board, Comment, Task


class UserSimpleSerializer(serializers.Serializer):
    """
    Simple serializer for user info in nested responses.
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
    Serializer for board list view.
    Includes member count, ticket count, and task statistics.
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
    Serializer for task comments.
    Displays author name, creation date, and content.
    """
    author = serializers.CharField(source="author.userprofile.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task detail view.
    Includes nested assignee and reviewer data.
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
    Nested serializer for tasks without board field to match board detail response.
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
    Serializer for board detail view.
    Includes members and tasks with full information.
    """
    members = UserSimpleSerializer(many=True, read_only=True)
    tasks = TaskNestedSerializer(many=True, read_only=True)
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating board.
    Allows updating title and members.
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
    Requires title and optional members list.
    """
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )

    class Meta:
        model = Board
        fields = ["title", "members"]

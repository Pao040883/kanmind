# 1. Standard library
from datetime import datetime

# 2. Third-party
from django.contrib.auth.models import User
from django.db import models


class Board(models.Model):
    """
    Kanban board model representing a collaborative workspace for task management.
    
    A board serves as the main container for organizing tasks. Each board has:
    - One owner (the user who created the board)
    - Multiple members (users who can access and manage tasks)
    - Multiple tasks (the actual work items in the board)
    
    Attributes:
        title (CharField): Name of the board (max 255 characters)
        owner (ForeignKey): The user who owns the board (CASCADE on delete, related_name="owned_boards")
        members (ManyToManyField): Users who are members of this board (related_name="board_memberships")
        created_at (DateTimeField): Timestamp of board creation (auto-populated)
        updated_at (DateTimeField): Timestamp of last board update (auto-updated)
    
    Related Names:
        owned_boards: Accessible from User as user_instance.owned_boards.all()
        board_memberships: Accessible from User as user_instance.board_memberships.all()
    
    Meta:
        Ordered by most recent board creation date (-created_at).
    
    Note:
        The owner is automatically added as a member and can manage the board.
        Board members can view, create, and modify tasks within the board.
    """
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_boards")
    members = models.ManyToManyField(User, related_name="board_memberships")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} (Owner: {self.owner.username})"


class Task(models.Model):
    """
    Task model representing a work item within a kanban board.
    
    Tasks are the core work units in the kanban system. Each task:
    - Belongs to exactly one board
    - Can be assigned to a board member for work
    - Can have a reviewer assigned for quality assurance
    - Tracks its creation source (created_by)
    - Has a lifecycle status (to-do → in-progress → review → done)
    - Has a priority level (low, medium, high)
    - Can have optional description and due date
    - Can have multiple comments attached
    
    Attributes:
        board (ForeignKey): The board this task belongs to (CASCADE on delete, related_name="tasks")
        title (CharField): Task name/title (max 255 characters)
        description (TextField): Detailed task description (optional, null/blank allowed)
        status (CharField): Current task status - choices: "to-do", "in-progress", "review", "done" (default: "to-do")
        priority (CharField): Task priority - choices: "low", "medium", "high" (default: "medium")
        assignee (ForeignKey): Board member assigned to work on the task (SET_NULL if user deleted, related_name="assigned_tasks")
        reviewer (ForeignKey): Board member responsible for reviewing the task (SET_NULL if user deleted, related_name="reviewing_tasks")
        created_by (ForeignKey): The user who created the task (CASCADE on delete, related_name="created_tasks")
        due_date (DateField): Optional deadline for task completion (null/blank allowed)
        created_at (DateTimeField): Timestamp of task creation (auto-populated)
        updated_at (DateTimeField): Timestamp of last task update (auto-updated)
    
    Related Names:
        tasks: Accessible from Board as board_instance.tasks.all()
        assigned_tasks: Accessible from User as user_instance.assigned_tasks.all()
        reviewing_tasks: Accessible from User as user_instance.reviewing_tasks.all()
        created_tasks: Accessible from User as user_instance.created_tasks.all()
        comments: Accessible as task_instance.comments.all()
    
    Meta:
        Ordered by most recent task creation date (-created_at).
    
    Note:
        Both assignee and reviewer are optional (nullable) as tasks can be unassigned initially.
        The created_by field is CASCADE (unlike assignee/reviewer) because task creator info is critical.
    """
    STATUS_CHOICES = [
        ("to-do", "To Do"),
        ("in-progress", "In Progress"),
        ("review", "Review"),
        ("done", "Done"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="to-do")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewing_tasks"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_tasks"
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Comment(models.Model):
    """
    Comment model for task discussions and feedback.
    
    Comments allow team members to collaborate and provide feedback on tasks.
    Each comment is associated with exactly one task and has an author.
    
    Attributes:
        task (ForeignKey): The task this comment belongs to (CASCADE on delete, related_name="comments")
        author (ForeignKey): The user who wrote the comment (CASCADE on delete, related_name="task_comments")
        content (TextField): The text content of the comment
        created_at (DateTimeField): Timestamp of comment creation (auto-populated)
        updated_at (DateTimeField): Timestamp of last comment update (auto-updated)
    
    Related Names:
        comments: Accessible from Task as task_instance.comments.all()
        task_comments: Accessible from User as user_instance.task_comments.all()
    
    Meta:
        Ordered chronologically by creation date (created_at) - earliest first.
    
    Note:
        If a comment author is deleted, their comments are also deleted (CASCADE).
        Comments maintain chronological order for readability in task discussions.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

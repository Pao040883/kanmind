# 1. Third-party
from django.contrib import admin

# 2. Local
from .models import Board, Comment, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """
    Admin interface for Board model.
    
    Provides staff access to manage kanban boards and their members.
    
    Display Configuration (list_display):
        - title: Board name
        - owner: User who owns the board
        - created_at: When the board was created
    
    Filtering (list_filter):
        - created_at: Filter boards by creation date
    
    Search (search_fields):
        - title: Search by board name
        - owner__username: Search by owner's username
    
    Member Management (filter_horizontal):
        - members: Many-to-many relation widget for easy member selection
        - Provides a side-by-side picker for adding/removing board members
    
    Read-Only Fields (readonly_fields):
        - created_at: Board creation timestamp (auto-generated)
        - updated_at: Board last update timestamp (auto-updated)
    
    Features:
        - View all boards and their owners
        - Add/remove board members using filter_horizontal widget
        - Search boards by name or owner
        - Filter by creation date for reporting
        - See when boards were created/updated
    
    Note:
        Owner is automatically a member
        Bulk member management is possible via the filter_horizontal widget
    """
    list_display = ["title", "owner", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["title", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["members"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    
    Provides staff access to manage tasks within boards.
    
    Display Configuration (list_display):
        - title: Task name/title
        - board: Board the task belongs to
        - status: Current task status (to-do, in-progress, review, done)
        - priority: Task priority level (low, medium, high)
        - assignee: User assigned to the task
        - created_at: When the task was created
    
    Filtering (list_filter):
        - status: Filter by task status
        - priority: Filter by task priority
        - created_at: Filter by creation date
        - board: Filter by board membership
    
    Search (search_fields):
        - title: Search by task title
        - description: Search by task description text
    
    Read-Only Fields (readonly_fields):
        - created_at: Task creation timestamp (auto-generated)
        - updated_at: Task last update timestamp (auto-updated)
    
    Features:
        - View all tasks with status and priority
        - Bulk edit tasks across boards
        - Filter by status/priority for reporting
        - Search tasks by title or description
        - See task assignments and timelines
    
    Note:
        Assignee and reviewer are optional (can be null)
        created_by is the task creator (CASCADE on delete)
        Tasks are deleted when the board is deleted
    """
    list_display = ["title", "board", "status", "priority", "assignee", "created_at"]
    list_filter = ["status", "priority", "created_at", "board"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin interface for Comment model.
    
    Provides staff access to manage task comments and discussions.
    
    Display Configuration (list_display):
        - author: User who wrote the comment
        - task: Task the comment is associated with
        - created_at: When the comment was created
    
    Filtering (list_filter):
        - created_at: Filter by comment date
    
    Search (search_fields):
        - content: Search by comment text
        - author__username: Search by author's username
    
    Read-Only Fields (readonly_fields):
        - created_at: Comment creation timestamp (auto-generated)
        - updated_at: Comment last update timestamp (auto-updated)
    
    Features:
        - View all comments and discussions
        - Filter comments by date
        - Search comments by content or author
        - Monitor task discussion activity
        - Track comment chronology
    
    Note:
        Comments are ordered chronologically (created_at)
        Comments are deleted when the task is deleted (CASCADE)
        Comments are deleted when the author is deleted (CASCADE)
        Comments cannot be edited (not exposed in API)
    """
    list_display = ["author", "task", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "author__username"]
    readonly_fields = ["created_at", "updated_at"]


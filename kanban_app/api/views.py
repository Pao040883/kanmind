# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

# 3. Local
from kanban_app.api.permissions import (
    IsAuthenticated,
    IsBoardMember,
    IsBoardOwner,
    IsCommentAuthor,
    IsTaskBoardMember,
    IsTaskCreatorOrBoardOwner,
)
from kanban_app.api.serializers import (
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardListSerializer,
    BoardUpdateSerializer,
    CommentSerializer,
    TaskSerializer,
)
from kanban_app.api.utils import (
    check_board_permission,
    get_board_or_error,
    process_task_creation,
    update_task_assignees,
    update_task_fields,
    validate_board_membership,
    validate_serializer_and_respond,
)
from kanban_app.models import Board, Comment, Task


class BoardViewSet(ModelViewSet):
    """
    Kanban board management viewset with full CRUD operations.
    
    Provides endpoints for listing, creating, retrieving, updating, and deleting boards.
    Only shows boards the user owns or is a member of.
    
    Endpoints:
        GET /api/boards/ - List user's boards
        POST /api/boards/ - Create new board
        GET /api/boards/{id}/ - Retrieve board details with members and tasks
        PATCH /api/boards/{id}/ - Update board title and/or members
        DELETE /api/boards/{id}/ - Delete board (owner only)
    
    HTTP Methods Allowed:
        GET, POST, PATCH, DELETE (PUT not allowed - use PATCH for partial updates)
    
    Authentication:
        Required (IsAuthenticated) - All operations require authentication
    
    Serializers:
        list: BoardListSerializer (summary with counts)
        create: BoardCreateSerializer (input validation)
        retrieve: BoardDetailSerializer (full details with members and tasks)
        update: BoardUpdateSerializer (for PATCH operations)
    
    Queryset:
        Filtered to boards where user is owner OR member
        Uses distinct() to avoid duplicates
    
    Permissions:
        - list/retrieve: Any board member or owner
        - create: Any authenticated user
        - update (PATCH): Any board member or owner
        - destroy (DELETE): Board owner only
    
    Note:
        Board owner is automatically added as a member.
        Members can be updated via PATCH with members list.
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            return BoardListSerializer
        elif self.action == "create":
            return BoardCreateSerializer
        elif self.action == "update":
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(members=user) | Board.objects.filter(owner=user)

    def list(self, request, *args, **kwargs):
        """GET /api/boards/ - List user's boards"""
        queryset = self.get_queryset().distinct()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """POST /api/boards/ - Create new board"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            board = Board.objects.create(
                title=serializer.validated_data["title"],
                owner=request.user,
            )
            members = serializer.validated_data.get("members", [])
            board.members.set(members)
            output_serializer = BoardListSerializer(board)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """GET /api/boards/{id}/ - Get board with tasks"""
        board_id = kwargs.get("pk")
        try:
            board = Board.objects.get(id=board_id)
            if board.owner != request.user and request.user not in board.members.all():
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = self.get_serializer(board)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Board.DoesNotExist:
            return Response(
                {"error": "Board not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def update(self, request, *args, **kwargs):
        """PATCH /api/boards/{id}/ - Update board members"""
        board_id = kwargs.get("pk")
        try:
            board = Board.objects.get(id=board_id)
            if board.owner != request.user and request.user not in board.members.all():
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = self.get_serializer(board, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output_serializer = BoardUpdateSerializer(board)
                return Response(output_serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Board.DoesNotExist:
            return Response(
                {"error": "Board not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/boards/{id}/ - Delete board"""
        board_id = kwargs.get("pk")
        try:
            board = Board.objects.get(id=board_id)
            if board.owner != request.user:
                return Response(
                    {"error": "Only owner can delete board"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            board.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Board.DoesNotExist:
            return Response(
                {"error": "Board not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class TaskListAssignedView(APIView):
    """
    List all tasks assigned to the current user.
    
    GET /api/tasks/assigned-to-me/
    
    Returns all tasks where the current user is the assignee.
    Includes full task details (status, priority, dates, etc.).
    
    Success Response (200 OK):
        [
            {
                "id": 1,
                "board": 5,
                "title": "Design new dashboard",
                "description": "...",
                "status": "in-progress",
                "priority": "high",
                "assignee": { "id": 2, "email": "...", "fullname": "..." },
                "reviewer": { ... },
                "due_date": "2024-12-20",
                "comments_count": 3
            },
            ...
        ]
    
    Authentication:
        Required (IsAuthenticated) - Must be logged in
    
    Filter:
        Only returns tasks where assignee == current user
    
    Used In:
        Dashboard view showing user's assigned work items
        Task management personal list
    
    Permissions:
        IsAuthenticated - Any authenticated user can see their assigned tasks
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assignee=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskListReviewingView(APIView):
    """
    List all tasks where the current user is the reviewer.
    
    GET /api/tasks/reviewing/
    
    Returns all tasks where the current user is assigned as the reviewer.
    Useful for QA/review workflows where users need to approve work.
    
    Success Response (200 OK):
        [
            {
                "id": 2,
                "board": 5,
                "title": "Code review - API endpoints",
                "description": "...",
                "status": "review",
                "priority": "medium",
                "assignee": { "id": 1, "email": "...", "fullname": "..." },
                "reviewer": { "id": 2, "email": "...", "fullname": "..." },
                "due_date": "2024-12-18",
                "comments_count": 5
            },
            ...
        ]
    
    Authentication:
        Required (IsAuthenticated) - Must be logged in
    
    Filter:
        Only returns tasks where reviewer == current user
    
    Used In:
        QA/review dashboard showing pending reviews
        Code review queue management
    
    Permissions:
        IsAuthenticated - Any authenticated user can see their review tasks
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(reviewer=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskViewSet(ModelViewSet):
    """
    Task management viewset with create, update, and delete operations.
    
    Provides endpoints for creating, updating, and deleting tasks within boards.
    Tasks can only be created/modified by board members.
    
    Endpoints:
        POST /api/tasks/ - Create new task
        PATCH /api/tasks/{id}/ - Update task
        DELETE /api/tasks/{id}/ - Delete task
    
    HTTP Methods Allowed:
        POST, PATCH, DELETE (GET not allowed - use board detail for task retrieval)
    
    Authentication:
        Required (IsAuthenticated) - All operations require authentication
    
    Serializer:
        TaskSerializer - Used for all operations (create, update, read response)
    
    Queryset:
        All tasks (filtering by permission)
    
    Permissions:
        - create: User must be a member of the target board
        - update (PATCH): User must be a member of the board
        - destroy (DELETE): Task creator or board owner only
    
    Validation:
        - assignee_id: If provided, assignee must be board member
        - reviewer_id: If provided, reviewer must be board member
        - status: Must be one of valid status choices
        - priority: Must be one of valid priority choices
    
    Error Handling:
        400: Invalid board, assignee, reviewer, or validation errors
        403: Permission denied (not board member/owner)
        404: Task/board not found
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    http_method_names = ["post", "patch", "delete"]

    def get_queryset(self):
        return Task.objects.all()

    def create(self, request, *args, **kwargs):
        """POST /api/tasks/ - Create task"""
        serializer = self.get_serializer(data=request.data)
        error = validate_serializer_and_respond(serializer)
        if error:
            return error
        
        board, error = get_board_or_error(request.data.get("board"))
        if error:
            return error
        
        error = check_board_permission(board, request.user)
        if error:
            return error
        
        task, error = process_task_creation(board, serializer.validated_data, request.data, request.user)
        if error:
            return error
        
        output_serializer = TaskSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/tasks/{id}/ - Update task"""
        try:
            task = Task.objects.get(id=kwargs.get("pk"))
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        error = check_board_permission(task.board, request.user)
        if error:
            return error
        
        serializer = self.get_serializer(task, data=request.data, partial=True)
        error = validate_serializer_and_respond(serializer)
        if error:
            return error
        
        error = update_task_assignees(task, request.data)
        if error:
            return error
        
        update_task_fields(task, serializer.validated_data)
        output_serializer = TaskSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/tasks/{id}/ - Delete task"""
        try:
            task = Task.objects.get(id=kwargs.get("pk"))
            if task.created_by != request.user and task.board.owner != request.user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class CommentListCreateView(APIView):
    """
    List and create comments on a specific task.
    
    GET /api/tasks/{task_id}/comments/
    List all comments on a task (ordered chronologically).
    
    POST /api/tasks/{task_id}/comments/
    Add a new comment to a task.
    
    Path Parameters:
        task_id (int): ID of the task to comment on
    
    GET Response (200 OK):
        [
            {
                "id": 1,
                "created_at": "2024-12-17T10:30:00Z",
                "author": "John Doe",
                "content": "Great start on this feature!"
            },
            ...
        ]
    
    POST Request Body (JSON):
        {
            "content": "I have a question about the implementation..."
        }
    
    POST Success Response (201 Created):
        {
            "id": 2,
            "created_at": "2024-12-17T11:00:00Z",
            "author": "Jane Smith",
            "content": "I have a question about the implementation..."
        }
    
    Authentication:
        Required (IsAuthenticated) - Must be logged in
    
    Permissions:
        - GET: User must be a board member
        - POST: User must be a board member
    
    Error Responses:
        400: Missing content in POST request
        403: Permission denied (not board member)
        404: Task not found
    
    Ordering:
        Comments are ordered chronologically by creation date (earliest first).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            board = task.board
            if request.user not in board.members.all() and board.owner != request.user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            comments = task.comments.all().order_by("created_at")
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            board = task.board
            if request.user not in board.members.all() and board.owner != request.user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            content = request.data.get("content")
            if not content:
                return Response(
                    {"error": "Content is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            comment = Comment.objects.create(
                task=task,
                author=request.user,
                content=content,
            )
            serializer = CommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class CommentDeleteView(APIView):
    """
    Delete a specific comment from a task.
    
    DELETE /api/tasks/{task_id}/comments/{comment_id}/
    
    Removes a comment from a task. Only the comment author can delete it.
    
    Path Parameters:
        task_id (int): ID of the task containing the comment
        comment_id (int): ID of the comment to delete
    
    Success Response (204 No Content):
        (empty response body)
    
    Authentication:
        Required (IsAuthenticated) - Must be logged in
    
    Permissions:
        - DELETE: Only the comment author can delete the comment
    
    Error Responses:
        403: Permission denied (not comment author)
        404: Task or comment not found
    
    Note:
        Comments are soft-deleted (actually removed from database).
        Maintains comment thread history through comment IDs and timestamps.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, task_id, comment_id):
        try:
            task = Task.objects.get(id=task_id)
            comment = Comment.objects.get(id=comment_id, task=task)
            if comment.author != request.user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (Task.DoesNotExist, Comment.DoesNotExist):
            return Response(
                {"error": "Task or comment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

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
from kanban_app.models import Board, Comment, Task


class BoardViewSet(ModelViewSet):
    """
    ViewSet for board operations.
    List, Create, Retrieve, Update, Destroy boards.
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
    GET /api/tasks/assigned-to-me/
    Get all tasks assigned to current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assignee=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskListReviewingView(APIView):
    """
    GET /api/tasks/reviewing/
    Get all tasks where user is reviewer.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(reviewer=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskViewSet(ModelViewSet):
    """
    ViewSet for task operations.
    Create, Retrieve, Update, Destroy tasks.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    http_method_names = ["post", "patch", "delete"]

    def get_queryset(self):
        return Task.objects.all()

    def create(self, request, *args, **kwargs):
        """POST /api/tasks/ - Create task"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            board_id = request.data.get("board")
            try:
                board = Board.objects.get(id=board_id)
                if request.user not in board.members.all() and board.owner != request.user:
                    return Response(
                        {"error": "Permission denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                assignee = None
                if "assignee_id" in request.data and request.data["assignee_id"]:
                    try:
                        assignee = User.objects.get(id=request.data["assignee_id"])
                        if assignee not in board.members.all():
                            return Response(
                                {"error": "Assignee not in board members"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    except User.DoesNotExist:
                        return Response(
                            {"error": "Assignee not found"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                reviewer = None
                if "reviewer_id" in request.data and request.data["reviewer_id"]:
                    try:
                        reviewer = User.objects.get(id=request.data["reviewer_id"])
                        if reviewer not in board.members.all():
                            return Response(
                                {"error": "Reviewer not in board members"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    except User.DoesNotExist:
                        return Response(
                            {"error": "Reviewer not found"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                task = Task.objects.create(
                    board=board,
                    title=serializer.validated_data["title"],
                    description=serializer.validated_data.get("description"),
                    status=serializer.validated_data.get("status", "to-do"),
                    priority=serializer.validated_data.get("priority", "medium"),
                    assignee=assignee,
                    reviewer=reviewer,
                    due_date=serializer.validated_data.get("due_date"),
                    created_by=request.user,
                )
                output_serializer = TaskSerializer(task)
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            except Board.DoesNotExist:
                return Response(
                    {"error": "Board not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/tasks/{id}/ - Update task"""
        try:
            task = Task.objects.get(id=kwargs.get("pk"))
            board = task.board
            if request.user not in board.members.all() and board.owner != request.user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = self.get_serializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                assignee_id = request.data.get("assignee_id")
                if assignee_id:
                    try:
                        assignee = User.objects.get(id=assignee_id)
                        if assignee not in board.members.all():
                            return Response(
                                {"error": "Assignee not in board members"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        task.assignee = assignee
                    except User.DoesNotExist:
                        return Response(
                            {"error": "Assignee not found"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                reviewer_id = request.data.get("reviewer_id")
                if reviewer_id:
                    try:
                        reviewer = User.objects.get(id=reviewer_id)
                        if reviewer not in board.members.all():
                            return Response(
                                {"error": "Reviewer not in board members"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        task.reviewer = reviewer
                    except User.DoesNotExist:
                        return Response(
                            {"error": "Reviewer not found"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                task.title = serializer.validated_data.get("title", task.title)
                task.description = serializer.validated_data.get("description", task.description)
                task.status = serializer.validated_data.get("status", task.status)
                task.priority = serializer.validated_data.get("priority", task.priority)
                task.due_date = serializer.validated_data.get("due_date", task.due_date)
                task.save()

                output_serializer = TaskSerializer(task)
                return Response(output_serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

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
    GET /api/tasks/{task_id}/comments/
    POST /api/tasks/{task_id}/comments/
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
    DELETE /api/tasks/{task_id}/comments/{comment_id}/
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

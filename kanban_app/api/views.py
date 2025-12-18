# 1. Standard library

# 2. Third-party
from django.shortcuts import get_object_or_404
from rest_framework import status
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
    TaskUpdateSerializer,
)
from kanban_app.api.utils import (
    check_board_permission,
    get_board_or_error,
    process_task_creation,
    update_task_assignees,
    update_task_fields,
    validate_serializer,
)
from kanban_app.models import Board, Comment, Task


class BoardViewSet(ModelViewSet):
    """
    Board CRUD operations with dynamic serializers per action.
    
    List action filters to user's boards only.
    Delete restricted to board owner via get_permissions().
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            return BoardListSerializer
        elif self.action == "create":
            return BoardCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_queryset(self):
        queryset = Board.objects.select_related('owner')
        
        # For list action, filter to user's boards only
        if self.action == 'list':
            user = self.request.user
            queryset = queryset.filter(members=user) | queryset.filter(owner=user)
            queryset = queryset.prefetch_related('members', 'tasks').distinct()
        # For retrieve/update/destroy, return all boards and let permissions handle access control
        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'members__profile',
                'tasks__assignee__profile',
                'tasks__reviewer__profile'
            )
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save(owner=request.user)
        output_serializer = BoardListSerializer(board)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        board = self.get_object()
        serializer = self.get_serializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        board = self.get_object()
        serializer = self.get_serializer(instance=board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        board = self.get_object()
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated(), IsBoardOwner()]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            return [IsAuthenticated(), IsBoardMember()]
        return [IsAuthenticated()]


class TaskListAssignedView(APIView):
    """
    List all tasks where user is assignee.
    
    Used for "My Tasks" view in dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assignee=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskListReviewingView(APIView):
    """
    List all tasks where user is reviewer.
    
    Used for "Review Queue" view in dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(reviewer=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskViewSet(ModelViewSet):
    """
    Task CRUD operations with member validation.
    
    Delete restricted to task creator or board owner via IsTaskCreatorOrBoardOwner.
    Assignee/reviewer must be board members (validated in utils).
    """
    serializer_class = TaskSerializer
    http_method_names = ["post", "patch", "delete"]

    def get_queryset(self):
        return Task.objects.select_related(
            'board',
            'board__owner',
            'assignee__profile',
            'reviewer__profile',
            'created_by'
        ).prefetch_related('comments')

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        elif self.action == 'partial_update':
            return [IsAuthenticated(), IsTaskBoardMember()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        validate_serializer(serializer)
        
        board = get_board_or_error(request.data.get("board"))
        check_board_permission(board, request.user)
        
        task = process_task_creation(board, serializer.validated_data, request.data, request.user)
        output_serializer = TaskSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        
        serializer = self.get_serializer(task, data=request.data, partial=True)
        validate_serializer(serializer)
        
        update_task_assignees(task, request.data)
        update_task_fields(task, serializer.validated_data)
        
        output_serializer = TaskUpdateSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentListCreateView(APIView):
    """
    List and create comments for a task.
    
    Requires board membership (owner or member) via IsTaskBoardMember.
    Comments ordered chronologically for conversation flow.
    """
    permission_classes = [IsAuthenticated, IsTaskBoardMember]

    def get(self, request, task_id):
        task = get_object_or_404(Task.objects.select_related('board', 'board__owner').prefetch_related('board__members'), id=task_id)
        self.check_object_permissions(request, task)
        
        comments = task.comments.select_related('author__profile').order_by("created_at")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        task = get_object_or_404(Task.objects.select_related('board', 'board__owner').prefetch_related('board__members'), id=task_id)
        self.check_object_permissions(request, task)
        
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    """
    Delete comment endpoint.
    
    Delete restricted to comment author via IsCommentAuthor permission.
    """
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def delete(self, request, task_id, comment_id):
        task = get_object_or_404(Task, id=task_id)
        comment = get_object_or_404(Comment.objects.select_related('author'), id=comment_id, task=task)
        self.check_object_permissions(request, comment)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# 1. Third-party
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

# 2. Local
from auth_app.models import UserProfile
from kanban_app.models import Board, Comment, Task


class BoardListTest(TestCase):
    """Test board list endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1@example.com",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2@example.com",
            email="user2@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user1, fullname="User One")
        UserProfile.objects.create(user=self.user2, fullname="User Two")
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        self.board1 = Board.objects.create(title="Board 1", owner=self.user1)
        self.board1.members.add(self.user1)
        self.board2 = Board.objects.create(title="Board 2", owner=self.user2)
        self.board2.members.add(self.user2, self.user1)

    def test_list_boards_success(self):
        """Test listing user's boards."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/boards/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_boards_unauthenticated(self):
        """Test listing boards without authentication."""
        response = self.client.get("/api/boards/")
        self.assertEqual(response.status_code, 401)


class BoardDeleteTest(TestCase):
    """Test board delete endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        self.token = Token.objects.create(user=self.user)

        self.board = Board.objects.create(title="Test Board", owner=self.user)
        self.board.members.add(self.user)

    def test_delete_board_success(self):
        """Test successful board deletion."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.delete(f"/api/boards/{self.board.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Board.objects.filter(id=self.board.id).exists())

    def test_delete_board_not_owner(self):
        """Test deleting board as non-owner."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        token = Token.objects.create(user=other_user)
        self.board.members.add(other_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.delete(f"/api/boards/{self.board.id}/")
        self.assertEqual(response.status_code, 403)


class TaskListTest(TestCase):
    """Test task list endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        self.token = Token.objects.create(user=self.user)

        self.board = Board.objects.create(title="Test Board", owner=self.user)
        self.board.members.add(self.user)

        self.task1 = Task.objects.create(
            board=self.board,
            title="Assigned Task",
            description="Task assigned to me",
            status="to-do",
            priority="high",
            assignee=self.user,
            created_by=self.user,
        )
        self.task2 = Task.objects.create(
            board=self.board,
            title="Review Task",
            description="Task for review",
            status="review",
            priority="medium",
            reviewer=self.user,
            created_by=self.user,
        )

    def test_list_assigned_tasks(self):
        """Test listing tasks assigned to user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get("/api/tasks/assigned-to-me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_reviewing_tasks(self):
        """Test listing tasks for review."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get("/api/tasks/reviewing/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_tasks_unauthenticated(self):
        """Test listing tasks without authentication."""
        response = self.client.get("/api/tasks/assigned-to-me/")
        self.assertEqual(response.status_code, 401)


class TaskCreateTest(TestCase):
    """Test task creation endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        self.token = Token.objects.create(user=self.user)

        self.board = Board.objects.create(title="Test Board", owner=self.user)
        self.board.members.add(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_task_success(self):
        """Test successful task creation."""
        data = {
            "board": self.board.id,
            "title": "New Task",
            "description": "Task description",
            "status": "to-do",
            "priority": "high",
            "due_date": "2025-02-25",
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "New Task")

    def test_create_task_not_member(self):
        """Test creating task as non-member."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        data = {
            "board": self.board.id,
            "title": "Hacked Task",
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 403)


class TaskDeleteTest(TestCase):
    """Test task delete endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        self.token = Token.objects.create(user=self.user)

        self.board = Board.objects.create(title="Test Board", owner=self.user)
        self.board.members.add(self.user)

        self.task = Task.objects.create(
            board=self.board,
            title="Test Task",
            created_by=self.user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_delete_task_success(self):
        """Test successful task deletion."""
        response = self.client.delete(f"/api/tasks/{self.task.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())


class CommentTest(TestCase):
    """Test comment endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        self.token = Token.objects.create(user=self.user)

        self.board = Board.objects.create(title="Test Board", owner=self.user)
        self.board.members.add(self.user)

        self.task = Task.objects.create(
            board=self.board,
            title="Test Task",
            created_by=self.user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_comments_success(self):
        """Test listing task comments."""
        response = self.client.get(f"/api/tasks/{self.task.id}/comments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_create_comment_success(self):
        """Test creating a comment."""
        data = {"content": "This is a comment"}
        response = self.client.post(
            f"/api/tasks/{self.task.id}/comments/", data
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["content"], "This is a comment")

    def test_delete_comment_success(self):
        """Test deleting a comment."""
        comment = Comment.objects.create(
            task=self.task, author=self.user, content="Test comment"
        )
        response = self.client.delete(
            f"/api/tasks/{self.task.id}/comments/{comment.id}/"
        )
        self.assertEqual(response.status_code, 204)

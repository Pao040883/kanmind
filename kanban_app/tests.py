# 1. Standard library

# 2. Third-party
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

# 3. Local
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


class BoardCreateTest(TestCase):
    """Test board creation endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user, fullname="Test User")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_board_success(self):
        """Test successful board creation."""
        data = {"title": "New Board", "members": []}
        response = self.client.post("/api/boards/", data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "New Board")
        self.assertEqual(response.data["owner_id"], self.user.id)

    def test_create_board_with_members(self):
        """Test board creation with members."""
        user2 = User.objects.create_user(
            username="user2@example.com",
            email="user2@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=user2, fullname="User Two")
        data = {"title": "Board with Members", "members": [user2.id]}
        response = self.client.post("/api/boards/", data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["member_count"], 1)

    def test_create_board_missing_title(self):
        """Test board creation without title."""
        data = {"members": []}
        response = self.client.post("/api/boards/", data)
        self.assertEqual(response.status_code, 400)


class BoardRetrieveTest(TestCase):
    """Test board retrieve endpoint."""

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

    def test_retrieve_board_success(self):
        """Test retrieving board details."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(f"/api/boards/{self.board.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Test Board")

    def test_retrieve_board_not_member(self):
        """Test retrieving board as non-member."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        token = Token.objects.create(user=other_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(f"/api/boards/{self.board.id}/")
        self.assertEqual(response.status_code, 403)

    def test_retrieve_board_not_found(self):
        """Test retrieving nonexistent board."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get("/api/boards/999/")
        self.assertEqual(response.status_code, 404)


class BoardUpdateTest(TestCase):
    """Test board update endpoint."""

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

        self.board = Board.objects.create(title="Test Board", owner=self.user1)
        self.board.members.add(self.user1)

    def test_update_board_success(self):
        """Test successful board update."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        data = {"title": "Updated Board", "members": [self.user2.id]}
        response = self.client.patch(f"/api/boards/{self.board.id}/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Board")

    def test_update_board_not_owner(self):
        """Test updating board as non-owner."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        token = Token.objects.create(user=other_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        data = {"title": "Hacked Board"}
        response = self.client.patch(f"/api/boards/{self.board.id}/", data)
        self.assertEqual(response.status_code, 403)


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

    def test_create_task_invalid_status(self):
        """Test creating task with invalid status."""
        data = {
            "board": self.board.id,
            "title": "Invalid Task",
            "status": "invalid-status",
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 400)


class TaskUpdateTest(TestCase):
    """Test task update endpoint."""

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
            status="to-do",
            created_by=self.user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_update_task_success(self):
        """Test successful task update."""
        data = {"title": "Updated Task", "status": "in-progress"}
        response = self.client.patch(f"/api/tasks/{self.task.id}/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Task")
        self.assertEqual(response.data["status"], "in-progress")

    def test_update_task_not_member(self):
        """Test updating task as non-member."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        data = {"status": "done"}
        response = self.client.patch(f"/api/tasks/{self.task.id}/", data)
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

    def test_delete_task_not_creator(self):
        """Test deleting task as non-creator."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        token = Token.objects.create(user=other_user)
        self.board.members.add(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.delete(f"/api/tasks/{self.task.id}/")
        self.assertEqual(response.status_code, 403)


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

    def test_create_comment_empty_content(self):
        """Test creating comment with empty content."""
        data = {"content": ""}
        response = self.client.post(
            f"/api/tasks/{self.task.id}/comments/", data
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_comment_success(self):
        """Test deleting a comment."""
        comment = Comment.objects.create(
            task=self.task, author=self.user, content="Test comment"
        )
        response = self.client.delete(
            f"/api/tasks/{self.task.id}/comments/{comment.id}/"
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_comment_not_author(self):
        """Test deleting comment as non-author."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=other_user, fullname="Other User")
        self.board.members.add(other_user)

        comment = Comment.objects.create(
            task=self.task, author=other_user, content="Other's comment"
        )
        response = self.client.delete(
            f"/api/tasks/{self.task.id}/comments/{comment.id}/"
        )
        self.assertEqual(response.status_code, 403)

    def test_comment_on_nonexistent_task(self):
        """Test commenting on nonexistent task."""
        data = {"content": "Comment"}
        response = self.client.post("/api/tasks/999/comments/", data)
        self.assertEqual(response.status_code, 404)

class TaskAssigneeReviewerTest(TestCase):
    """Test task assignee and reviewer validation."""

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
        self.user3 = User.objects.create_user(
            username="user3@example.com",
            email="user3@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=self.user1, fullname="User One")
        UserProfile.objects.create(user=self.user2, fullname="User Two")
        UserProfile.objects.create(user=self.user3, fullname="User Three")
        self.token1 = Token.objects.create(user=self.user1)

        self.board = Board.objects.create(title="Test Board", owner=self.user1)
        self.board.members.add(self.user1, self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")

    def test_create_task_assignee_not_member(self):
        """Test creating task with non-member assignee."""
        data = {
            "board": self.board.id,
            "title": "Task",
            "assignee_id": self.user3.id,
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("not in board members", str(response.data))

    def test_create_task_reviewer_not_member(self):
        """Test creating task with non-member reviewer."""
        data = {
            "board": self.board.id,
            "title": "Task",
            "reviewer_id": self.user3.id,
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 400)

    def test_create_task_both_assignee_reviewer(self):
        """Test creating task with both assignee and reviewer."""
        data = {
            "board": self.board.id,
            "title": "Task",
            "description": "Test",
            "assignee_id": self.user1.id,
            "reviewer_id": self.user2.id,
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["assignee"]["id"], self.user1.id)
        self.assertEqual(response.data["reviewer"]["id"], self.user2.id)

    def test_update_task_assignee_invalid_id(self):
        """Test updating task with invalid assignee ID."""
        task = Task.objects.create(
            board=self.board,
            title="Task",
            created_by=self.user1,
        )
        data = {"assignee_id": 999}
        response = self.client.patch(f"/api/tasks/{task.id}/", data)
        self.assertEqual(response.status_code, 400)

    def test_update_task_reviewer_invalid_id(self):
        """Test updating task with invalid reviewer ID."""
        task = Task.objects.create(
            board=self.board,
            title="Task",
            created_by=self.user1,
        )
        data = {"reviewer_id": 999}
        response = self.client.patch(f"/api/tasks/{task.id}/", data)
        self.assertEqual(response.status_code, 400)


class TaskPermissionTest(TestCase):
    """Test task permissions and access control."""

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

        self.board = Board.objects.create(title="Test Board", owner=self.user1)
        self.board.members.add(self.user1)

        self.task = Task.objects.create(
            board=self.board,
            title="Task",
            created_by=self.user1,
        )

    def test_update_task_not_member(self):
        """Test updating task as non-board member."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        data = {"title": "Updated"}
        response = self.client.patch(f"/api/tasks/{self.task.id}/", data)
        self.assertEqual(response.status_code, 403)

    def test_delete_task_not_creator_not_owner(self):
        """Test deleting task as non-creator and non-owner."""
        self.board.members.add(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        response = self.client.delete(f"/api/tasks/{self.task.id}/")
        self.assertEqual(response.status_code, 403)

    def test_create_task_board_not_found(self):
        """Test creating task with nonexistent board."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        data = {
            "board": 999,
            "title": "Task",
        }
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, 404)

    def test_update_nonexistent_task(self):
        """Test updating nonexistent task."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        data = {"title": "Updated"}
        response = self.client.patch("/api/tasks/999/", data)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_task(self):
        """Test deleting nonexistent task."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.delete("/api/tasks/999/")
        self.assertEqual(response.status_code, 404)


class CommentPermissionTest(TestCase):
    """Test comment permissions and access control."""

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

        self.board = Board.objects.create(title="Test Board", owner=self.user1)
        self.board.members.add(self.user1)

        self.task = Task.objects.create(
            board=self.board,
            title="Task",
            created_by=self.user1,
        )

    def test_list_comments_not_member(self):
        """Test listing comments as non-board member."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        response = self.client.get(f"/api/tasks/{self.task.id}/comments/")
        self.assertEqual(response.status_code, 403)

    def test_create_comment_not_member(self):
        """Test creating comment as non-board member."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token2.key}")
        data = {"content": "Comment"}
        response = self.client.post(f"/api/tasks/{self.task.id}/comments/", data)
        self.assertEqual(response.status_code, 403)

    def test_delete_comment_nonexistent(self):
        """Test deleting nonexistent comment."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.delete(f"/api/tasks/{self.task.id}/comments/999/")
        self.assertEqual(response.status_code, 404)
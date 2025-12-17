# 1. Third-party
from django.urls import path
from rest_framework.routers import DefaultRouter

# 2. Local
from kanban_app.api import views

router = DefaultRouter()
router.register(r"boards", views.BoardViewSet, basename="board")
router.register(r"tasks", views.TaskViewSet, basename="task")

app_name = "kanban_api"

urlpatterns = [
    path("tasks/assigned-to-me/", views.TaskListAssignedView.as_view(), name="tasks_assigned"),
    path("tasks/reviewing/", views.TaskListReviewingView.as_view(), name="tasks_reviewing"),
    path(
        "tasks/<int:task_id>/comments/",
        views.CommentListCreateView.as_view(),
        name="comment_list_create",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        views.CommentDeleteView.as_view(),
        name="comment_delete",
    ),
] + router.urls

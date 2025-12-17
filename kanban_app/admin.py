# 1. Third-party
from django.contrib import admin

# 2. Local
from .models import Board, Comment, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["title", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["members"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "board", "status", "priority", "assignee", "created_at"]
    list_filter = ["status", "priority", "created_at", "board"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "task", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "author__username"]
    readonly_fields = ["created_at", "updated_at"]

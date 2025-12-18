# 1. Third-party
from django.contrib import admin

# 2. Local
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["fullname", "user", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["fullname", "user__email"]
    readonly_fields = ["created_at", "updated_at"]


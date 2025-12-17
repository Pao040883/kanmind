# 1. Third-party
from django.contrib import admin

# 2. Local
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    
    Provides staff access to view, search, and manage user profiles.
    
    Display Configuration (list_display):
        - fullname: User's full name
        - user: Link to Django User object
        - created_at: When the profile was created
    
    Filtering (list_filter):
        - created_at: Filter profiles by creation date
    
    Search (search_fields):
        - fullname: Search by user's full name
        - user__email: Search by user's email address
    
    Read-Only Fields (readonly_fields):
        - created_at: Profile creation timestamp (auto-generated)
        - updated_at: Profile last update timestamp (auto-updated)
    
    Features:
        - View all user profiles in a table
        - Search profiles by name or email
        - Filter by creation date for reporting
        - See when profiles were created/updated
    
    Note:
        User deletion is handled at Django User level (CASCADE)
        Modifying UserProfile also updates the updated_at timestamp
    """
    list_display = ["fullname", "user", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["fullname", "user__email"]
    readonly_fields = ["created_at", "updated_at"]


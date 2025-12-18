# KanMind Backend API

A Django REST Framework-based backend for the KanMind Kanban board application. This API provides endpoints for user authentication, board management, task tracking, and commenting.

## Features

- **User Authentication**: Token-based authentication with registration and login
- **Board Management**: Create, retrieve, update, and delete Kanban boards
- **Task Management**: Full CRUD operations for tasks with status tracking and priority levels
- **Comments**: Add, view, and delete comments on tasks
- **Permissions**: Role-based access control for board members and owners
- **Admin Interface**: Django admin panel for managing all resources

## Tech Stack

- **Django 6.0**: Web framework
- **Django REST Framework 3.16**: API framework
- **Python 3.13**: Programming language
- **SQLite**: Database (development)

## Installation

### Prerequisites

- Python 3.8 or higher
- Git

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Pao040883/kanmind.git
   cd kanmind
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   
   # Linux/Mac:
   source venv/bin/activate
   
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   
   # Windows CMD:
   venv\Scripts\activate.bat
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin panel):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication

**Login und Registrierung**

- `POST /api/registration/` - Register a new user
- `POST /api/login/` - Login and get authentication token

### Boards

**Alles zur Bearbeitung, Erstellung und Abruf von Boards**

- `GET /api/boards/` - List user's boards
- `POST /api/boards/` - Create a new board
- `GET /api/boards/{id}/` - Get board details with tasks
- `PATCH /api/boards/{id}/` - Update board members
- `DELETE /api/boards/{id}/` - Delete board
- `GET /api/email-check/` - Check if email exists 

### Tasks

**Alles zur Bearbeitung, Erstellung und Abruf von Tasks**

- `GET /api/tasks/assigned-to-me/` - Get tasks assigned to current user
- `GET /api/tasks/reviewing/` - Get tasks where user is reviewer
- `POST /api/tasks/` - Create a new task
- `PATCH /api/tasks/{id}/` - Update task details
- `DELETE /api/tasks/{id}/` - Delete task
- `GET /api/tasks/{task_id}/comments/` - Get task comments
- `POST /api/tasks/{task_id}/comments/` - Create a comment
- `DELETE /api/tasks/{task_id}/comments/{comment_id}/` - Delete comment

## Utility Functions

Common business logic is extracted into utility modules for reusability and maintainability:

### `auth_app/api/utils.py`
- `create_token_response()`: Build authentication response with token and user info
- `get_user_and_profile()`: Fetch user and profile by email with error handling
- `authenticate_and_get_token()`: Handle user authentication and token creation

### `kanban_app/api/utils.py`
- **Validation**: `validate_board_membership()`, `validate_and_get_assignee()`, `validate_and_get_reviewer()`
- **Creation**: `create_task_from_data()` - Persist new task with all fields
- **Updates**: `update_task_fields()`, `update_task_assignee_if_provided()`, `update_task_reviewer_if_provided()`
- **Permissions**: `check_board_permission()` - Verify user board access
- **Orchestration**: `process_task_creation()`, `validate_task_assignees()`, `update_task_assignees()` - Multi-step operations

## Authentication

The API uses Token Authentication. Include the token in the `Authorization` header:

```bash
Authorization: Token <your-token>
```

Example:
```bash
curl -H "Authorization: Token abc123def456" http://127.0.0.1:8000/api/boards/
```

## Project Structure

```
backend/
├── core/                    # Main Django project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration
├── auth_app/               # Authentication application
│   ├── api/
│   │   ├── serializers.py  # API serializers
│   │   ├── views.py        # API views
│   │   ├── urls.py         # URL routing
│   │   ├── permissions.py  # Custom permissions
│   │   └── utils.py        # Authentication helpers
│   ├── models.py           # User profile model
│   └── admin.py            # Admin configuration
├── kanban_app/             # Kanban board application
│   ├── api/
│   │   ├── serializers.py  # Serializers for boards, tasks, comments
│   │   ├── views.py        # ViewSets and API views
│   │   ├── urls.py         # URL routing
│   │   ├── permissions.py  # Board and task permissions
│   │   └── utils.py        # Board, task, and validation helpers
│   ├── models.py           # Board, Task, Comment models
│   └── admin.py            # Admin configuration
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

## Code Standards

This project follows these conventions:

- **PEP 8**: Python style guide
- **Max function length**: 14 lines
- **Model naming**: PascalCase (e.g., `UserProfile`, `Board`)
- **Field naming**: snake_case (e.g., `fullname`, `created_at`)
- **Imports**: Grouped and sorted (stdlib → third-party → local)
- **Views**: Use ViewSets for CRUD operations, APIView for custom endpoints
- **Serializers**: Explicit field declaration, custom validation methods
- **Permissions**: Role-based access control with clear permission classes
- **Utility Functions**: Proportional docstrings (1-4 lines for helpers, more for complex logic)
- **Error Handling**: Tuple returns `(result, error_response)` for consistent error propagation

## Environment Variables

Currently, no environment variables are required for development. For production, consider:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False
- `ALLOWED_HOSTS`: List of allowed hosts
- `DATABASE_URL`: Database connection string

## Testing

Run tests with:
```bash
python manage.py test
```

Coverage wird mit coverage.py gemessen; optional anzeigen mit:
```bash
coverage run manage.py test
coverage report
```

## Admin Panel

Access the Django admin panel at `http://127.0.0.1:8000/admin/` with superuser credentials.

Available models:
- User Profiles
- Boards
- Tasks
- Comments

## License
This project is for educational purposes.

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.

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
   source venv/Scripts/activate  # On Windows
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

- `POST /api/registration/` - Register a new user
- `POST /api/login/` - Login and get authentication token
- `GET /api/email-check/` - Check if email exists (requires authentication)

### Boards

- `GET /api/boards/` - List user's boards
- `POST /api/boards/` - Create a new board
- `GET /api/boards/{id}/` - Get board details with tasks
- `PATCH /api/boards/{id}/` - Update board members
- `DELETE /api/boards/{id}/` - Delete board

### Tasks

- `GET /api/tasks/assigned-to-me/` - Get tasks assigned to current user
- `GET /api/tasks/reviewing/` - Get tasks where user is reviewer
- `POST /api/tasks/` - Create a new task
- `PATCH /api/tasks/{id}/` - Update task details
- `DELETE /api/tasks/{id}/` - Delete task

### Comments

- `GET /api/tasks/{task_id}/comments/` - Get task comments
- `POST /api/tasks/{task_id}/comments/` - Create a comment
- `DELETE /api/tasks/{task_id}/comments/{comment_id}/` - Delete comment

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
│   │   └── permissions.py  # Custom permissions
│   ├── models.py           # User profile model
│   └── admin.py            # Admin configuration
├── kanban_app/             # Kanban board application
│   ├── api/
│   │   ├── serializers.py  # Serializers for boards, tasks, comments
│   │   ├── views.py        # ViewSets and API views
│   │   ├── urls.py         # URL routing
│   │   └── permissions.py  # Board and task permissions
│   ├── models.py           # Board, Task, Comment models
│   └── admin.py            # Admin configuration
├── manage.py               # Django management script
├── db.sqlite3              # SQLite database (created after migration)
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

## Admin Panel

Access the Django admin panel at `http://127.0.0.1:8000/admin/` with superuser credentials.

Available models:
- User Profiles
- Boards
- Tasks
- Comments

## License

See LICENSE file for details.

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.

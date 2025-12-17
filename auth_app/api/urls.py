# 1. Third-party
from django.urls import path

# 2. Local
from auth_app.api import views

app_name = "auth_api"

urlpatterns = [
    path("registration/", views.RegistrationView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("email-check/", views.EmailCheckView.as_view(), name="email_check"),
]

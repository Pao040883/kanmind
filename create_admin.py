from django.contrib.auth.models import User
from auth_app.models import UserProfile

# Create superuser with E-Mail als Username, damit Login mit dem E-Mail-Feld funktioniert
email = "admin@example.com"
password = "admin"

# Falls schon vorhanden, nicht doppelt anlegen
user, created = User.objects.get_or_create(
	username=email,
	defaults={"email": email, "is_staff": True, "is_superuser": True},
)
if created:
	user.set_password(password)
	user.save()
	UserProfile.objects.create(user=user, fullname="Admin User")
	print("Admin user created successfully!")
else:
	print("Admin user already exists")

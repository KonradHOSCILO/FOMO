from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

class AppUserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(mail=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        if email is None:
            email = extra_fields.pop("username", None) or extra_fields.pop("mail", None)

        if not email:
            raise ValueError("Superuser email is required")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)

    mail = models.EmailField(unique=True, db_column="mail")
    created_at = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AppUserManager()

    USERNAME_FIELD = "mail"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.mail


class TaskGroup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_groups")
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=20, default="#5c6b7a")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "task_groups"
        unique_together = ("user", "name")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name} ({self.user})"


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "New (todo)"
        IN_PROGRESS = "in_progress", "W trakcie"
        DONE = "done", "Zrobione"
        ARCHIVED = "archived", "Archiwum"

    class Group(models.TextChoices):
        IMPORTANT = "Ważne", "Ważne"
        CLEANING = "Sprzątanie", "Sprzątanie"
        WORK = "Praca", "Praca"
        FRIENDS = "Znajomi", "Znajomi"
        FAMILY = "Rodzina", "Rodzina"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")

    group = models.CharField(max_length=255, choices=Group.choices, default=Group.IMPORTANT)

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)

    remind_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title


class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    filename = models.CharField(max_length=255)
    object_key = models.CharField(max_length=1024)
    file_url = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "attachments"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.filename

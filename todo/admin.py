from django.contrib import admin
from .models import Task, TaskGroup, Attachment


@admin.register(TaskGroup)
class TaskGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "color", "order", "created_at")
    search_fields = ("name", "user__mail")
    ordering = ("order", "id")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "group", "status", "remind_at", "created_at")
    list_filter = ("status", "group", "created_at")
    search_fields = ("title", "description", "user__mail")
    ordering = ("-created_at",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "filename", "object_key", "created_at")
    search_fields = ("filename", "object_key", "task__title")
    ordering = ("-created_at",)

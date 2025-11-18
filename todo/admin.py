from django.contrib import admin

from .models import Task, TaskGroup


@admin.register(TaskGroup)
class TaskGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "order")
    search_fields = ("name",)
    ordering = ("order", "name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "priority", "is_completed", "due_date", "created_at")
    list_filter = ("is_completed", "priority", "group", "repeat_frequency", "created_at")
    search_fields = ("title", "description")
    autocomplete_fields = ("group",)
    ordering = ("-created_at",)

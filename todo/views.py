from __future__ import annotations

# pyright: reportMissingImports=false

from urllib.parse import urlencode

from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import TaskForm, TaskGroupForm
from .models import Task, TaskGroup

DEFAULT_GROUPS = (
    ("Ważne", {"color": "#d13438"}),
    ("Powtarzalne", {"color": "#4ade80"}),
    ("Sprzątanie", {"color": "#0078d4"}),
)


def _coerce_group_id(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _redirect_with_view_params(view: str | None = None, group_id: int | None = None):
    """Simple redirect helper that preserves view and group filters."""
    url = reverse("task_list")
    params = {}
    if view:
        params["view"] = view
    if group_id:
        params["group"] = group_id
    if params:
        return redirect(f"{url}?{urlencode(params)}")
    return redirect(url)


def task_list(request):
    """
    Microsoft To-Do style task list view.
    """
    from datetime import date, timedelta
    from django.utils import timezone

    # Ensure default groups exist
    for name, defaults in DEFAULT_GROUPS:
        TaskGroup.objects.get_or_create(name=name, defaults=defaults)

    # Get view type (today, tomorrow, week, month)
    active_view = request.GET.get("view", "today")
    
    # Get active group filter
    active_group = _coerce_group_id(request.GET.get("group"))

    # SIMPLIFIED TASK QUERY - Always show tasks, filter by group and date view
    today = timezone.now().date()
    
    # Start with all tasks
    tasks_queryset = Task.objects.all()
    
    # Filter by group (sidebar filter) - if no group selected, show all
    if active_group:
        tasks_queryset = tasks_queryset.filter(group_id=active_group)
    
    # Filter by date view - SIMPLIFIED: Always include tasks without due dates
    # This ensures newly created tasks are always visible
    if active_view == "today":
        # Show tasks due today OR tasks without due date
        tasks_queryset = tasks_queryset.filter(
            Q(due_date__date=today) | Q(due_date__isnull=True)
        )
    elif active_view == "tomorrow":
        tomorrow = today + timedelta(days=1)
        # Show tasks due tomorrow OR tasks without due date
        tasks_queryset = tasks_queryset.filter(
            Q(due_date__date=tomorrow) | Q(due_date__isnull=True)
        )
    elif active_view == "week":
        week_end = today + timedelta(days=7)
        # Show tasks due in next 7 days OR tasks without due date
        tasks_queryset = tasks_queryset.filter(
            Q(due_date__date__range=[today, week_end]) | Q(due_date__isnull=True)
        )
    elif active_view == "month":
        month_end = today + timedelta(days=30)
        # Show tasks due in next 30 days OR tasks without due date
        tasks_queryset = tasks_queryset.filter(
            Q(due_date__date__range=[today, month_end]) | Q(due_date__isnull=True)
        )
    # If no view specified, show ALL tasks (no date filter)

    # Order tasks: priority (high first), then due date, then creation date
    tasks = list(tasks_queryset.order_by("-priority", "due_date", "-created_at"))
    
    # Get all groups
    groups = list(
        TaskGroup.objects.annotate(task_count=Count("tasks")).order_by("order", "name")
    )

    # If no groups exist, create defaults
    if not groups:
        for name, defaults in DEFAULT_GROUPS:
            group, _ = TaskGroup.objects.get_or_create(name=name, defaults=defaults)
            groups.append(group)
        groups = list(TaskGroup.objects.annotate(task_count=Count("tasks")).order_by("order", "name"))

    # Forms for creating new items (not used for task creation anymore, but kept for consistency)
    group_form = TaskGroupForm(prefix="group")

    # Handle POST requests
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_task":
            # SIMPLIFIED TASK CREATION - Direct model creation
            title = request.POST.get("task-title", "").strip()
            if title:
                # Get form data
                description = request.POST.get("task-description", "").strip()
                repeat_freq = request.POST.get("task-repeat_frequency", "none")
                group_id = request.POST.get("task-group", "").strip()
                
                # Create task directly
                task = Task.objects.create(
                    title=title,
                    description=description,
                    repeat_frequency=repeat_freq,
                    group_id=int(group_id) if group_id else None,
                    priority=Task.Priority.MEDIUM,
                )
                
                # Redirect to preserve current view and group filter
                redirect_url = reverse("task_list")
                params = {"view": active_view}
                if active_group:
                    params["group"] = active_group
                return redirect(f"{redirect_url}?{urlencode(params)}")
        elif action == "create_group":
            group_form = TaskGroupForm(request.POST, prefix="group")
            if group_form.is_valid():
                group_form.save()
                redirect_url = reverse("task_list")
                params = {"view": active_view}
                if active_group:
                    params["group"] = active_group
                return redirect(f"{redirect_url}?{urlencode(params)}")

    default_group_names = [name for name, _ in DEFAULT_GROUPS]
    
    context = {
        "tasks": tasks,
        "groups": groups,
        "active_view": active_view,
        "active_group": active_group,
        "group_form": group_form,
        "default_group_names": default_group_names,
    }
    return render(request, "todo/task_list.html", context)


def edit_task(request, task_id: int):
    """Simple task editing - only title, group, and repeat frequency."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Get current view and group from query params for redirect
    active_view = request.GET.get("view", "today")
    active_group = _coerce_group_id(request.GET.get("group"))
    
    form = TaskForm(request.POST or None, instance=task)

    if request.method == "POST" and form.is_valid():
        form.save()
        # If AJAX request, return success
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        # Otherwise redirect back to task list with current filters
        redirect_url = reverse("task_list")
        params = {"view": active_view}
        if active_group:
            params["group"] = active_group
        return redirect(f"{redirect_url}?{urlencode(params)}")

    # If AJAX request for form, return just the form HTML
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "todo/task_edit_form.html",
            {
                "task": task,
                "form": form,
                "query_string": request.GET.urlencode(),
            },
        )

    return render(
        request,
        "todo/task_edit.html",
        {
            "task": task,
            "form": form,
            "query_string": request.GET.urlencode(),
        },
    )


@require_POST
def toggle_task(request, task_id: int):
    """Toggle task completion status."""
    task = get_object_or_404(Task, pk=task_id)
    task.toggle_completion()
    view = request.GET.get("view", "today")
    group_id = _coerce_group_id(request.GET.get("group"))
    return _redirect_with_view_params(view, group_id)


@require_POST
def delete_task(request, task_id: int):
    """Delete a task."""
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    view = request.GET.get("view", "today")
    group_id = _coerce_group_id(request.GET.get("group"))
    return _redirect_with_view_params(view, group_id)


@require_POST
def move_task(request, task_id: int):
    """
    Przenieś zadanie do innej grupy i ustaw pozycję.
    """

    task = get_object_or_404(Task, pk=task_id)
    group_id = request.POST.get("group_id")
    position = request.POST.get("position")

    target_group = None
    if group_id:
        target_group = get_object_or_404(TaskGroup, pk=group_id)

    new_position = None
    if position:
        try:
            new_position = int(position)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Pozycja musi być liczbą całkowitą.")

    task.move_to(target_group, new_position)

    # Return JSON if requested
    if request.headers.get("Accept") == "application/json":
        groups = TaskGroup.objects.annotate(task_count=Count("tasks")).all()
        inbox_count = Task.objects.filter(group__isnull=True).count()
        return JsonResponse({
            "success": True,
            "groups": [{"id": g.id, "task_count": g.task_count} for g in groups],
            "inbox_count": inbox_count,
        })

    view = request.GET.get("view", "today")
    group_id = _coerce_group_id(request.GET.get("group"))
    return _redirect_with_view_params(view, group_id)


@require_POST
def delete_group(request, group_id: int):
    group = get_object_or_404(TaskGroup, pk=group_id)
    default_group_names = [name for name, _ in DEFAULT_GROUPS]
    if group.name in default_group_names:
        return redirect("task_list")
    group.delete()
    return redirect("task_list")


@require_POST
def edit_group(request, group_id: int):
    """Edit group color."""
    group = get_object_or_404(TaskGroup, pk=group_id)
    color = request.POST.get("color")
    if color:
        group.color = color
        group.save()
    return redirect("task_list")


@require_POST
def reorder_task(request, task_id: int):
    """Update task position for reordering."""
    task = get_object_or_404(Task, pk=task_id)
    new_position = request.POST.get("position")
    
    try:
        position = int(new_position) if new_position else 0
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid position"}, status=400)
    
    # Get all tasks in the same group with same completion status, ordered by current position
    tasks_in_group = list(
        Task.objects.filter(group=task.group, is_completed=task.is_completed)
        .exclude(pk=task.pk)
        .order_by("position", "-created_at")
    )
    
    # Remove task from list temporarily
    # Insert at new position
    tasks_in_group.insert(position, task)
    
    # Reassign positions sequentially
    for idx, t in enumerate(tasks_in_group, start=1):
        t.position = idx
        t.save(update_fields=["position"])
    
    return JsonResponse({"success": True})


@require_POST
def reorder_group(request, group_id: int):
    """Update group order for reordering."""
    group = get_object_or_404(TaskGroup, pk=group_id)
    new_order = request.POST.get("order")
    
    try:
        order = int(new_order) if new_order else 0
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid order"}, status=400)
    
    # Get all groups, ordered by current order
    groups = list(TaskGroup.objects.exclude(pk=group.pk).order_by("order", "name"))
    
    # Insert group at new position
    groups.insert(order, group)
    
    # Reassign orders sequentially
    for idx, g in enumerate(groups, start=1):
        g.order = idx
        g.save(update_fields=["order"])
    
    return JsonResponse({"success": True})

from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlencode

from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import TaskForm, TaskGroupForm
from .models import Task, TaskGroup


def _coerce_group_id(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _redirect_with_view_params(sort_by: str | None = None, group_id: int | None = None):
    group_id = _coerce_group_id(group_id)
    params = {}
    if sort_by and sort_by != "priority":
        params["sort"] = sort_by
    if group_id:
        params["group"] = group_id
    url = reverse("task_list")
    if params:
        return redirect(f"{url}?{urlencode(params)}")
    return redirect(url)


def task_list(request):
    """
    Strona główna z listą zadań i formularzem dodawania nowego zadania.
    """

    sort_by = request.GET.get("sort", "priority")
    group_id = _coerce_group_id(request.GET.get("group"))

    tasks_queryset = Task.objects.sorted(sort_by, group_id=group_id)
    tasks = list(tasks_queryset)
    spotlight_tasks = list(Task.objects.sorted("priority")[:5])
    groups = list(
        TaskGroup.objects.annotate(task_count=Count("tasks")).order_by("order", "name")
    )

    task_form = TaskForm(prefix="task")
    group_form = TaskGroupForm(prefix="group")
    query_params = {}
    if sort_by and sort_by != "priority":
        query_params["sort"] = sort_by
    if group_id:
        query_params["group"] = group_id
    query_string = urlencode(query_params)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_task":
            task_form = TaskForm(request.POST, prefix="task")
            if task_form.is_valid():
                task_form.save()
                return _redirect_with_view_params(sort_by, group_id)
        elif action == "create_group":
            group_form = TaskGroupForm(request.POST, prefix="group")
            if group_form.is_valid():
                group_form.save()
                return _redirect_with_view_params(sort_by, group_id)

    tasks_by_group: dict[int | None, list[Task]] = defaultdict(list)
    for task in tasks:
        tasks_by_group[task.group_id].append(task)

    if group_id:
        visible_groups = [group for group in groups if group.id == group_id]
    else:
        visible_groups = groups

    grouped_columns = [
        {
            "group": group,
            "tasks": tasks_by_group.get(group.id, []),
        }
        for group in visible_groups
    ]

    inbox_tasks = [] if group_id else tasks_by_group.get(None, [])
    inbox_total = Task.objects.filter(group__isnull=True).count()

    stats = {
        "total": len(tasks),
        "completed": sum(1 for task in tasks if task.is_completed),
        "high_priority": sum(1 for task in tasks if task.priority == Task.Priority.HIGH),
        "repeating": sum(
            1
            for task in tasks
            if task.repeat_frequency != Task.RepeatFrequency.NONE
        ),
    }

    context = {
            "tasks": tasks,
            "groups": groups,
            "grouped_columns": grouped_columns,
        "ungrouped_tasks": inbox_tasks,
        "ungrouped_count": inbox_total,
        "task_form": task_form,
        "group_form": group_form,
        "active_sort": sort_by,
        "active_group": group_id,
        "show_inbox_column": not group_id,
        "spotlight_tasks": spotlight_tasks,
        "stats": stats,
        "query_string": query_string,
    }
    return render(request, "todo/task_list.html", context)


def edit_task(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    sort_by = request.GET.get("sort")
    group_id = request.GET.get("group")
    form = TaskForm(request.POST or None, instance=task, prefix="task")

    if request.method == "POST" and form.is_valid():
        form.save()
        return _redirect_with_view_params(sort_by, group_id)

    return render(
        request,
        "todo/task_edit.html",
        {
            "task": task,
            "form": form,
            "active_sort": sort_by,
            "active_group": group_id,
            "query_string": urlencode(
                {k: v for k, v in (("sort", sort_by), ("group", group_id)) if v}
            ),
        },
    )


@require_POST
def toggle_task(request, task_id: int):
    """
    Oznacz zadanie jako zrobione / niezrobione.
    """

    task = get_object_or_404(Task, pk=task_id)
    task.toggle_completion()
    return _redirect_with_view_params(request.GET.get("sort"), request.GET.get("group"))


@require_POST
def delete_task(request, task_id: int):
    """
    Usuń zadanie.
    """
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return _redirect_with_view_params(request.GET.get("sort"), request.GET.get("group"))


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
    return _redirect_with_view_params(request.GET.get("sort"), request.GET.get("group"))

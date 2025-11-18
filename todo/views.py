from __future__ import annotations

# pyright: reportMissingImports=false

from collections import defaultdict
from urllib.parse import urlencode

from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import TaskForm, TaskGroupForm
from .models import Task, TaskGroup

DEFAULT_GROUPS = (
    (
        "Todo",
        {
            "color": "#7c8cff",
            "icon": "ph-list-checks",
        },
    ),
    (
        "Powtarzalne",
        {
            "color": "#4ade80",
            "icon": "ph-repeat",
        },
    ),
)


def _coerce_group_id(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _redirect_with_view_params(
    sort_by: str | None = None,
    group_id: int | None = None,
    extra_query: QueryDict | None = None,
):
    group_id = _coerce_group_id(group_id)
    params = QueryDict(mutable=True)
    if sort_by and sort_by != "priority":
        params.update({"sort": sort_by})
    if group_id:
        params.update({"group": group_id})
    if extra_query:
        for key in ("groups", "include_inbox", "view_all"):
            if key in extra_query:
                for value in extra_query.getlist(key):
                    params.appendlist(key, value)
    url = reverse("task_list")
    query_string = params.urlencode()
    if query_string:
        return redirect(f"{url}?{query_string}")
    return redirect(url)


def task_list(request):
    """
    Strona główna z listą zadań i formularzem dodawania nowego zadania.
    """

    sort_by = request.GET.get("sort", "priority")

    for name, defaults in DEFAULT_GROUPS:
        TaskGroup.objects.get_or_create(name=name, defaults=defaults)

    raw_groups = request.GET.getlist("groups")
    selected_group_ids: list[int] = []
    for value in raw_groups:
        try:
            selected_group_ids.append(int(value))
        except (TypeError, ValueError):
            continue

    include_inbox = request.GET.get("include_inbox") == "1"
    explicit_view_all = request.GET.get("view_all") == "1"

    if not raw_groups and not include_inbox and not explicit_view_all:
        show_all_groups = True
        include_inbox = True
    else:
        show_all_groups = explicit_view_all

    base_queryset = Task.objects.sorted(sort_by)
    if show_all_groups:
        include_inbox = True
        tasks_queryset = base_queryset
    else:
        filters = Q()
        if selected_group_ids:
            filters |= Q(group_id__in=selected_group_ids)
        if include_inbox:
            filters |= Q(group__isnull=True)
        tasks_queryset = base_queryset.filter(filters) if filters else base_queryset.none()

    tasks = list(tasks_queryset)
    spotlight_tasks = list(Task.objects.sorted("priority")[:5])
    groups = list(
        TaskGroup.objects.annotate(task_count=Count("tasks")).order_by("order", "name")
    )

    task_form = TaskForm(prefix="task")
    group_form = TaskGroupForm(prefix="group")
    query_params = QueryDict(mutable=True)
    if sort_by and sort_by != "priority":
        query_params.update({"sort": sort_by})
    if show_all_groups and explicit_view_all:
        query_params.update({"view_all": "1"})
    if not show_all_groups:
        if include_inbox:
            query_params.update({"include_inbox": "1"})
        for gid in selected_group_ids:
            query_params.appendlist("groups", str(gid))
    query_string = query_params.urlencode()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_task":
            task_form = TaskForm(request.POST, prefix="task")
            if task_form.is_valid():
                task_form.save()
                return _redirect_with_view_params(sort_by)
        elif action == "create_group":
            group_form = TaskGroupForm(request.POST, prefix="group")
            if group_form.is_valid():
                group_form.save()
                return _redirect_with_view_params(sort_by)

    tasks_by_group: dict[int | None, list[Task]] = defaultdict(list)
    for task in tasks:
        tasks_by_group[task.group_id].append(task)

    if show_all_groups:
        visible_groups = groups
    else:
        visible_groups = [group for group in groups if group.id in selected_group_ids]

    grouped_columns = [
        {
            "group": group,
            "tasks": tasks_by_group.get(group.id, []),
        }
        for group in visible_groups
    ]

    inbox_tasks = tasks_by_group.get(None, []) if (show_all_groups or include_inbox) else []
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
        "show_inbox_column": show_all_groups or include_inbox,
        "selected_group_ids": selected_group_ids,
        "include_inbox": include_inbox,
        "show_all_groups": show_all_groups,
        "spotlight_tasks": spotlight_tasks,
        "default_group_names": [name for name, _ in DEFAULT_GROUPS],
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
        return _redirect_with_view_params(sort_by, group_id, request.GET)

    return render(
        request,
        "todo/task_edit.html",
        {
            "task": task,
            "form": form,
            "active_sort": sort_by,
            "active_group": group_id,
            "query_string": request.GET.urlencode(),
        },
    )


@require_POST
def toggle_task(request, task_id: int):
    """
    Oznacz zadanie jako zrobione / niezrobione.
    """

    task = get_object_or_404(Task, pk=task_id)
    task.toggle_completion()
    return _redirect_with_view_params(
        request.GET.get("sort"),
        request.GET.get("group"),
        request.GET,
    )


@require_POST
def delete_task(request, task_id: int):
    """
    Usuń zadanie.
    """
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return _redirect_with_view_params(
        request.GET.get("sort"),
        request.GET.get("group"),
        request.GET,
    )


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

    return _redirect_with_view_params(
        request.GET.get("sort"),
        request.GET.get("group"),
        request.GET,
    )


@require_POST
def delete_group(request, group_id: int):
    group = get_object_or_404(TaskGroup, pk=group_id)
    if group.name in dict(DEFAULT_GROUPS):
        return _redirect_with_view_params(
            request.GET.get("sort"),
            request.GET.get("group"),
            request.GET,
        )
    group.delete()
    return _redirect_with_view_params(request.GET.get("sort"), None, request.GET)

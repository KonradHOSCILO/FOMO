from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from todo.forms import TaskCreateForm, RegisterForm, LoginForm
from todo.services.ovh_users import ensure_ovh_user
from todo.services.task_sql_service import create_task_sql
from todo.services.task_read_sql_service import list_tasks_with_attachments
from todo.services.task_sql_service import create_task_sql, delete_task_sql, update_task_sql


STATUS_LABELS = {
    "todo": "Do zrobienia",
    "in_progress": "W trakcie",
    "done": "Zrobione",
    "archived": "Archiwum",
}

GROUPS = ["Ważne", "Sprzątanie", "Praca", "Znajomi", "Rodzina"]

def register_view(request):
    if request.user.is_authenticated:
        return redirect("task_list")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()

        ensure_ovh_user(
            django_user_id=user.id,
            email=user.mail,
            password_hash=user.password,
        )

        login(request, user)
        return redirect("task_list")

    return render(request, "todo/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("task_list")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        return redirect("task_list")

    return render(request, "todo/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def task_list(request):
    selected_group = request.GET.get("group") or None
    if selected_group not in GROUPS:
        selected_group = None

    tasks = list_tasks_with_attachments(user_id=request.user.id, group=selected_group)
    form = TaskCreateForm()
    return render(
        request,
        "todo/task_list.html",
        {"tasks": tasks, "form": form, "groups": GROUPS, "selected_group": selected_group},
    )

@require_POST
@login_required
def update_task(request, task_id: int):
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    group = request.POST.get("group", "Ważne")
    status = request.POST.get("status", "todo")

    update_task_sql(
        user_id=request.user.id,
        task_id=task_id,
        title=title,
        description=description,
        group=group,
        status=status,
    )
    return redirect("task_list")


@require_POST
@login_required
def create_task(request):
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    group = request.POST.get("group", "Ważne")
    status = request.POST.get("status", "todo")
    upload = request.FILES.get("file")

    if upload and upload.size > 100 * 1024 * 1024:
        messages.error(request, "Plik jest za duży. Maksymalny rozmiar to 100 MB.")
        return redirect("task_list")

    if status not in ("todo", "in_progress", "done"):
        status = "todo"

    create_task_sql(
        user_id=request.user.id,
        title=title,
        description=description,
        group=group,
        status=status,
        upload=upload,
    )
    return redirect("task_list")


@require_POST
@login_required
def delete_task(request, task_id: int):
    delete_task_sql(user_id=request.user.id, task_id=task_id)
    return redirect("task_list")


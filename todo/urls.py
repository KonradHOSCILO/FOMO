from django.urls import path

from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("task/<int:task_id>/edit/", views.edit_task, name="edit_task"),
    path("task/<int:task_id>/toggle/", views.toggle_task, name="toggle_task"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("task/<int:task_id>/move/", views.move_task, name="move_task"),
]



from django.urls import path

from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("task/<int:task_id>/edit/", views.edit_task, name="edit_task"),
    path("task/<int:task_id>/toggle/", views.toggle_task, name="toggle_task"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("task/<int:task_id>/move/", views.move_task, name="move_task"),
    path("task/<int:task_id>/reorder/", views.reorder_task, name="reorder_task"),
    path("group/<int:group_id>/delete/", views.delete_group, name="delete_group"),
    path("group/<int:group_id>/edit/", views.edit_group, name="edit_group"),
    path("group/<int:group_id>/reorder/", views.reorder_group, name="reorder_group"),
]



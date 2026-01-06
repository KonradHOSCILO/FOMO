from django.urls import path
from todo import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("tasks/create/", views.create_task, name="create_task"),
    path("tasks/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("tasks/<int:task_id>/update/", views.update_task, name="update_task"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
]

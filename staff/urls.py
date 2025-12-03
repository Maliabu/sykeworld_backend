from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.CreateStaffView.as_view(), name="create_staff"),
    path("assign-task/", views.AssignTaskView.as_view(), name="assign_task"),
    path("all/", views.ListStaffView.as_view(), name="list_staff"),
    path("tasks/", views.ListTasksView.as_view(), name="list_tasks"),
]

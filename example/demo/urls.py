from django.urls import path

from demo import views

urlpatterns = [
    path("api/hello/", views.hello_view),
    path("api/add/", views.add_view),
    path("api/multiply/", views.multiply_view),
    path("api/tasks/submit/", views.submit_task_view),
    path("api/tasks/<str:task_id>/status/", views.task_status_view),
    path("api/modules/", views.list_modules_view),
]

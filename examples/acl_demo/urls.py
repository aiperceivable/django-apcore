"""URL routing for the django-apcore ACL demo."""

from django.urls import path

from . import views

urlpatterns = [
    path("orders", views.list_orders_view),
    path("orders/<int:order_id>", views.delete_order_view),
]

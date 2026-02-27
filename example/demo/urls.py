from django.urls import path

from demo.api import api

urlpatterns = [
    path("api/", api.urls),
]

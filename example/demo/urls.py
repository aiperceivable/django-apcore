from django.urls import path

from demo.api import api
from django_apcore.views import explorer_redirect

urlpatterns = [
    path("api/", api.urls),
    path("explorer/", explorer_redirect),
]

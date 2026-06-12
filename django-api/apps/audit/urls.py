from django.urls import path

from apps.accounts.views import admin_create_user
from apps.rag.views import metrics

urlpatterns = [
    path("users/", admin_create_user),
    path("metrics/", metrics),
]

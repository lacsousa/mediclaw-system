from django.urls import path
from .views import register, login, logout, refresh, me, admin_create_user

urlpatterns = [
    path("register/", register),
    path("login/", login),
    path("refresh/", refresh),
    path("logout/", logout),
    path("me/", me),
]

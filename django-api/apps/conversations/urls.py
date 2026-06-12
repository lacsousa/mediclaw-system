from django.urls import path

from .views import detail, list_create, stream, post_message

urlpatterns = [
    path("", list_create),
    path("<int:conv_id>/", detail),
    path("<int:conv_id>/messages/", post_message),
    path("<int:conv_id>/stream/", stream),
]

from django.urls import path

from .views import (
    delete_document,
    document_status,
    list_documents,
    upload,
)

urlpatterns = [
    path("upload/", upload),
    path("", list_documents),
    path("<int:doc_id>/status/", document_status),
    path("<int:doc_id>/", delete_document),
]

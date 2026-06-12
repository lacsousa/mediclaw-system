from django.urls import path
from . import views

urlpatterns = [
    path("", views.list_patients, name="patient-list"),
    path("<int:patient_id>/", views.patient_detail, name="patient-detail"),
]

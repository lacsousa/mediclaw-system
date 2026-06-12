from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import AppError
from apps.patients.models import Patient

from .models import ActivityLog, NutritionNote, SleepLog, WeightLog
from .serializers import (
    ActivityLogSerializer,
    NutritionNoteSerializer,
    SleepLogSerializer,
    WeightLogSerializer,
)
from .services.aggregate import summarize


def _get_patient_or_404(request, patient_id: int) -> Patient:
    """Obtém paciente garantindo ownership do médico autenticado."""
    try:
        return Patient.objects.get(pk=patient_id, doctor=request.user)
    except Patient.DoesNotExist:
        raise AppError("NOT_FOUND", "Paciente não encontrado.", 404)


class _PatientQuerysetMixin:
    """Filtra logs pelo patient_id passado como query param."""

    def get_queryset(self):
        patient_id = self.request.query_params.get("patient_id")
        if not patient_id:
            return super().get_queryset().none()
        _get_patient_or_404(self.request, int(patient_id))
        qs = super().get_queryset().filter(patient_id=patient_id)
        ts_field = self.timestamp_field
        from_ = self.request.query_params.get("from")
        to_ = self.request.query_params.get("to")
        if from_:
            qs = qs.filter(**{f"{ts_field}__gte": from_})
        if to_:
            qs = qs.filter(**{f"{ts_field}__lte": to_})
        return qs

    def perform_create(self, serializer):
        patient_id = self.request.data.get("patient_id")
        if not patient_id:
            from rest_framework import serializers
            raise serializers.ValidationError({"patient_id": "Obrigatório."})
        _get_patient_or_404(self.request, int(patient_id))
        serializer.save(patient_id=int(patient_id))


class WeightLogViewSet(_PatientQuerysetMixin, viewsets.ModelViewSet):
    queryset = WeightLog.objects.all()
    serializer_class = WeightLogSerializer
    permission_classes = [IsAuthenticated]
    timestamp_field = "measured_at"
    http_method_names = ["get", "post", "delete"]


class SleepLogViewSet(_PatientQuerysetMixin, viewsets.ModelViewSet):
    queryset = SleepLog.objects.all()
    serializer_class = SleepLogSerializer
    permission_classes = [IsAuthenticated]
    timestamp_field = "started_at"
    http_method_names = ["get", "post", "delete"]


class ActivityLogViewSet(_PatientQuerysetMixin, viewsets.ModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    timestamp_field = "performed_at"
    http_method_names = ["get", "post", "delete"]


class NutritionNoteViewSet(_PatientQuerysetMixin, viewsets.ModelViewSet):
    queryset = NutritionNote.objects.all()
    serializer_class = NutritionNoteSerializer
    permission_classes = [IsAuthenticated]
    timestamp_field = "logged_at"
    http_method_names = ["get", "post", "delete"]


@api_view(["GET"])
def health_summary(request):
    patient_id = request.query_params.get("patient_id")
    if not patient_id:
        raise AppError("VALIDATION_ERROR", "patient_id é obrigatório.", 400)
    _get_patient_or_404(request, int(patient_id))
    window = int(request.query_params.get("window", "7"))
    if window not in (7, 30):
        window = 7
    return Response(summarize(int(patient_id), window))

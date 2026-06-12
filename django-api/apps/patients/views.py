from django.db.models import Count, Max, OuterRef, Subquery
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import AppError
from apps.health_logs.models import WeightLog

from .models import Patient
from .serializers import PatientDetailSerializer, PatientListSerializer

PAGE_SIZE = 20


def _annotate_patients(qs):
    """Anota queryset de Patient com conversation_count, last_seen_at e latest_weight_kg."""
    latest_weight = (
        WeightLog.objects.filter(patient=OuterRef("pk"))
        .order_by("-measured_at")
        .values("value_kg")[:1]
    )
    return qs.annotate(
        conversation_count=Count(
            "conversations",
            filter=Q(conversations__deleted_at__isnull=True),
        ),
        last_seen_at=Max(
            "conversations__updated_at",
            filter=Q(conversations__deleted_at__isnull=True),
        ),
        latest_weight_kg=Subquery(latest_weight),
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_patients(request):
    page = int(request.GET.get("page", 1))
    offset = (page - 1) * PAGE_SIZE
    qs = _annotate_patients(Patient.objects.filter(doctor=request.user))
    total = qs.count()
    items = qs[offset: offset + PAGE_SIZE]
    has_next = offset + PAGE_SIZE < total
    return Response(
        {
            "results": PatientListSerializer(items, many=True).data,
            "count": total,
            "next": f"?page={page + 1}" if has_next else None,
        }
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def patient_detail(request, patient_id: int):
    try:
        patient = _annotate_patients(
            Patient.objects.filter(doctor=request.user)
        ).get(pk=patient_id)
    except Patient.DoesNotExist:
        raise AppError("NOT_FOUND", "Paciente não encontrado.", 404)

    if request.method == "GET":
        return Response(PatientDetailSerializer(patient).data)

    if request.method == "PATCH":
        s = PatientListSerializer(patient, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(PatientListSerializer(patient).data)

    if request.method == "DELETE":
        patient.delete()
        return Response(status=204)

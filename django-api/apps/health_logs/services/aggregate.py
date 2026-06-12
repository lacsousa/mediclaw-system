from datetime import timedelta

from django.db.models import Avg, Sum
from django.utils import timezone

from ..models import ActivityLog, NutritionNote, SleepLog, WeightLog


def summarize(patient_id: int, window_days: int = 7) -> dict:
    since = timezone.now() - timedelta(days=window_days)

    sleep_qs = SleepLog.objects.filter(patient_id=patient_id, started_at__gte=since)
    avg_sleep = sleep_qs.aggregate(a=Avg("duration_hours"))["a"]
    avg_quality = sleep_qs.aggregate(a=Avg("quality_score"))["a"]

    latest_weight = (
        WeightLog.objects.filter(patient_id=patient_id)
        .order_by("-measured_at")
        .values_list("value_kg", flat=True)
        .first()
    )
    first_weight = (
        WeightLog.objects.filter(patient_id=patient_id, measured_at__gte=since)
        .order_by("measured_at")
        .values_list("value_kg", flat=True)
        .first()
    )
    weight_trend = (
        float(latest_weight - first_weight)
        if (latest_weight and first_weight)
        else None
    )

    total_activity = (
        ActivityLog.objects.filter(
            patient_id=patient_id, performed_at__gte=since
        ).aggregate(s=Sum("duration_min"))["s"]
        or 0
    )

    last_notes = list(
        NutritionNote.objects.filter(patient_id=patient_id)
        .order_by("-logged_at")
        .values_list("note", flat=True)[:3]
    )

    return {
        "window_days": window_days,
        "avg_sleep_hours": float(avg_sleep) if avg_sleep is not None else None,
        "avg_sleep_quality": float(avg_quality) if avg_quality is not None else None,
        "latest_weight_kg": float(latest_weight) if latest_weight is not None else None,
        "weight_trend_kg": weight_trend,
        "total_activity_min": int(total_activity),
        "last_nutrition_notes": last_notes,
    }

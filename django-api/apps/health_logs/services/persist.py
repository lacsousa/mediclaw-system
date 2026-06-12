"""Persistência de health logs sem request HTTP (captura via chat)."""

from datetime import datetime
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from ..models import ActivityLog, NutritionNote, SleepLog, WeightLog

DEFAULT_SLEEP_QUALITY = 5
MIN_NUTRITION_NOTE_LEN = 10


def _validate_not_future(dt: datetime, field_name: str) -> datetime:
    if dt > timezone.now():
        raise serializers.ValidationError(f"{field_name} não pode ser no futuro.")
    return dt


def persist_weight_log(patient_id: int, data: dict[str, Any]) -> dict[str, Any]:
    value_kg = float(data["value_kg"])
    if not (20 <= value_kg <= 400):
        raise serializers.ValidationError(
            "Peso fora do intervalo plausível (20–400 kg)."
        )
    measured_at = data.get("measured_at") or timezone.now()
    _validate_not_future(measured_at, "measured_at")
    obj = WeightLog.objects.create(
        patient_id=patient_id, value_kg=value_kg, measured_at=measured_at
    )
    return {
        "id": obj.id,
        "value_kg": float(obj.value_kg),
        "measured_at": obj.measured_at.isoformat(),
    }


def persist_sleep_log(patient_id: int, data: dict[str, Any]) -> dict[str, Any]:
    duration = float(data["duration_hours"])
    if duration <= 0 or duration > 24:
        raise serializers.ValidationError("duration_hours deve estar entre 0 e 24.")
    quality = int(data.get("quality_score") or DEFAULT_SLEEP_QUALITY)
    if not (1 <= quality <= 10):
        raise serializers.ValidationError("quality_score deve estar entre 1 e 10.")
    started_at = data.get("started_at") or timezone.now()
    _validate_not_future(started_at, "started_at")
    obj = SleepLog.objects.create(
        patient_id=patient_id,
        duration_hours=duration,
        quality_score=quality,
        started_at=started_at,
    )
    return {
        "id": obj.id,
        "duration_hours": float(obj.duration_hours),
        "quality_score": obj.quality_score,
        "started_at": obj.started_at.isoformat(),
    }


def persist_activity_log(patient_id: int, data: dict[str, Any]) -> dict[str, Any]:
    duration_min = int(data["duration_min"])
    if duration_min < 1:
        raise serializers.ValidationError("duration_min deve ser ≥ 1.")
    activity_type = (data.get("type") or "").strip()
    if not activity_type:
        raise serializers.ValidationError("type é obrigatório.")
    if len(activity_type) > 40:
        activity_type = activity_type[:40]
    performed_at = data.get("performed_at") or timezone.now()
    _validate_not_future(performed_at, "performed_at")
    obj = ActivityLog.objects.create(
        patient_id=patient_id,
        type=activity_type,
        duration_min=duration_min,
        performed_at=performed_at,
    )
    return {
        "id": obj.id,
        "type": obj.type,
        "duration_min": obj.duration_min,
        "performed_at": obj.performed_at.isoformat(),
    }


def persist_nutrition_note(patient_id: int, data: dict[str, Any]) -> dict[str, Any]:
    note = (data.get("note") or "").strip()
    if len(note) < MIN_NUTRITION_NOTE_LEN:
        raise serializers.ValidationError(
            f"note deve ter pelo menos {MIN_NUTRITION_NOTE_LEN} caracteres."
        )
    if len(note) > 1000:
        raise serializers.ValidationError("note excede 1000 caracteres.")
    logged_at = data.get("logged_at") or timezone.now()
    _validate_not_future(logged_at, "logged_at")
    obj = NutritionNote.objects.create(
        patient_id=patient_id, note=note, logged_at=logged_at
    )
    return {"id": obj.id, "note": obj.note, "logged_at": obj.logged_at.isoformat()}

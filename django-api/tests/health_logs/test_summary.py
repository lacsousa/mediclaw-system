import pytest
from django.utils import timezone
from datetime import timedelta

from apps.health_logs.models import (
    ActivityLog,
    NutritionNote,
    SleepLog,
    WeightLog,
)
from apps.health_logs.services.aggregate import summarize
from apps.patients.models import Patient


@pytest.fixture
def patient(user, db):
    return Patient.objects.create(doctor=user, first_name="João")


@pytest.fixture
def other_patient(other_user, db):
    return Patient.objects.create(doctor=other_user, first_name="Maria")


@pytest.mark.django_db
class TestSummary:
    def test_summary_with_no_logs_returns_nulls(self, patient):
        result = summarize(patient.id, window_days=7)
        assert result["avg_sleep_hours"] is None
        assert result["avg_sleep_quality"] is None
        assert result["latest_weight_kg"] is None
        assert result["weight_trend_kg"] is None
        assert result["total_activity_min"] == 0
        assert result["last_nutrition_notes"] == []

    def test_summary_aggregates_within_window(self, patient, freezer):
        with freezer("2026-05-21 12:00:00"):
            SleepLog.objects.create(
                patient=patient,
                duration_hours=8.0,
                quality_score=9,
                started_at=timezone.now() - timedelta(days=2),
            )
            SleepLog.objects.create(
                patient=patient,
                duration_hours=7.0,
                quality_score=8,
                started_at=timezone.now() - timedelta(days=1),
            )
            WeightLog.objects.create(
                patient=patient,
                value_kg=80.0,
                measured_at=timezone.now() - timedelta(days=3),
            )
            WeightLog.objects.create(
                patient=patient,
                value_kg=78.5,
                measured_at=timezone.now(),
            )
            ActivityLog.objects.create(
                patient=patient,
                type="running",
                duration_min=30,
                performed_at=timezone.now() - timedelta(days=1),
            )
            NutritionNote.objects.create(
                patient=patient,
                note="Breakfast",
                logged_at=timezone.now(),
            )

            result = summarize(patient.id, window_days=7)
            assert result["avg_sleep_hours"] == 7.5
            assert result["avg_sleep_quality"] == 8.5
            assert result["latest_weight_kg"] == 78.5
            assert result["weight_trend_kg"] == -1.5
            assert result["total_activity_min"] == 30
            assert len(result["last_nutrition_notes"]) == 1

    def test_summary_excludes_other_patients(self, patient, other_patient):
        now = timezone.now()
        SleepLog.objects.create(
            patient=other_patient,
            duration_hours=8.0,
            quality_score=9,
            started_at=now - timedelta(days=1),
        )
        result = summarize(patient.id, window_days=7)
        assert result["avg_sleep_hours"] is None

    def test_weight_log_validates_range(self, auth_client, user):
        patient = Patient.objects.create(doctor=user, first_name="Teste")
        data = {
            "patient_id": patient.id,
            "value_kg": 15,
            "measured_at": timezone.now().isoformat(),
        }
        response = auth_client.post(
            "/api/v1/health/weight/",
            data=data,
            format="json",
        )
        assert response.status_code == 400
        assert "Peso fora do intervalo" in str(response.data)

    def test_user_cannot_delete_another_patients_log(self, auth_client, other_user):
        now = timezone.now()
        other_patient = Patient.objects.create(
            doctor=other_user, first_name="Outro"
        )
        log = WeightLog.objects.create(
            patient=other_patient,
            value_kg=80.0,
            measured_at=now,
        )
        response = auth_client.delete(f"/api/v1/health/weight/{log.id}/")
        assert response.status_code == 404

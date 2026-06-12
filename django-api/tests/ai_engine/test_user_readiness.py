from datetime import date

import pytest

from apps.health_logs.models import WeightLog
from apps.patients.models import Patient
from apps.ai_engine.skills.user_readiness import get_user_readiness


@pytest.mark.django_db
class TestGetUserReadiness:
    def test_none_patient_id_returns_all_missing(self):
        readiness = get_user_readiness(None)
        assert readiness.is_complete is False
        assert readiness.missing_name is True
        assert set(readiness.missing_profile_fields) == {
            "birth_date",
            "biological_sex",
            "height_cm",
        }
        assert readiness.missing_weight_log is True

    def test_patient_with_no_data(self, user):
        patient = Patient.objects.create(doctor=user, first_name="João")
        readiness = get_user_readiness(patient.id)
        assert readiness.is_complete is False
        assert readiness.missing_name is False
        assert set(readiness.missing_profile_fields) == {
            "birth_date",
            "biological_sex",
            "height_cm",
        }
        assert readiness.missing_weight_log is True

    def test_missing_name_when_first_name_empty(self, user):
        patient = Patient.objects.create(doctor=user, first_name="")
        readiness = get_user_readiness(patient.id)
        assert readiness.missing_name is True
        assert "nome" in readiness.missing_labels_pt()
        assert readiness.is_complete is False

    def test_partial_profile(self, user):
        patient = Patient.objects.create(
            doctor=user,
            first_name="Maria",
            birth_date=date(1990, 1, 1),
        )
        readiness = get_user_readiness(patient.id)
        assert readiness.is_complete is False
        assert readiness.missing_profile_fields == ["biological_sex", "height_cm"]
        assert readiness.missing_weight_log is True

    def test_complete_patient(self, user):
        patient = Patient.objects.create(
            doctor=user,
            first_name="Carlos",
            birth_date=date(1990, 1, 1),
            biological_sex="M",
            height_cm=175,
        )
        WeightLog.objects.create(
            patient=patient, value_kg=80.0, measured_at="2025-01-01T10:00:00Z"
        )
        readiness = get_user_readiness(patient.id)
        assert readiness.is_complete is True
        assert readiness.missing_profile_fields == []
        assert readiness.missing_weight_log is False

    def test_missing_labels_pt_with_all_missing(self):
        readiness = get_user_readiness(None)
        labels = readiness.missing_labels_pt()
        assert labels[0] == "nome"
        assert "data de nascimento" in labels
        assert "peso atual (kg)" in labels

    def test_nonexistent_patient_id_returns_all_missing(self):
        readiness = get_user_readiness(99999)
        assert readiness.is_complete is False
        assert readiness.missing_name is True

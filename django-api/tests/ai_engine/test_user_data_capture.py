from datetime import date

import pytest

from apps.conversations.models import Conversation
from apps.health_logs.models import ActivityLog, NutritionNote, SleepLog, WeightLog
from apps.patients.models import Patient
from apps.ai_engine.services.capture_rules import parse_rules
from apps.ai_engine.services.user_data_capture import capture_from_message


@pytest.fixture(autouse=True)
def disable_capture_llm(monkeypatch):
    monkeypatch.setenv("DATA_CAPTURE_LLM", "false")


@pytest.fixture
def conv(db, user):
    return Conversation.objects.create(doctor=user, title="Nova conversa")


@pytest.fixture
def conv_with_patient(db, user):
    patient = Patient.objects.create(doctor=user, first_name="João")
    conv = Conversation.objects.create(doctor=user, patient=patient, title="João")
    return conv, patient


@pytest.mark.django_db
class TestCaptureRules:
    def test_parse_profile_and_weight(self):
        data = parse_rules("Tenho 1,75 m de altura, 80 kg, nasci 15/03/1990, sou homem")
        assert data.profile.height_cm == 175
        assert data.profile.birth_date == date(1990, 3, 15)
        assert data.profile.biological_sex == "M"
        assert data.weight.value_kg == 80.0

    def test_parse_sleep(self):
        data = parse_rules("Dormi 7 horas, qualidade 8")
        assert data.sleep.duration_hours == 7.0
        assert data.sleep.quality_score == 8

    def test_parse_activity(self):
        data = parse_rules("Corri 30 minutos hoje")
        assert data.activity.type == "corrida"
        assert data.activity.duration_min == 30

    def test_parse_nutrition(self):
        data = parse_rules("Almocei frango grelhado com arroz e salada")
        assert data.nutrition.note
        assert "frango" in data.nutrition.note.lower()


@pytest.mark.django_db
class TestCaptureFromMessage:
    def test_name_creates_patient(self, user, conv):
        result = capture_from_message(conv.id, user.id, "Me chamo Maria Silva")
        assert "name" in result.saved
        assert result.patient_id is not None
        patient = Patient.objects.get(pk=result.patient_id)
        assert patient.first_name == "Maria Silva"
        assert patient.doctor == user

    def test_full_onboarding_with_name(self, user, conv):
        result = capture_from_message(
            conv.id, user.id,
            "Me chamo João, tenho 1,75 m, 80 kg, nasci 15/03/1990, sou homem",
        )
        assert "name" in result.saved
        assert "profile" in result.saved
        assert "weight_log" in result.saved
        assert result.patient_id is not None
        patient = Patient.objects.get(pk=result.patient_id)
        assert patient.height_cm == 175
        assert patient.biological_sex == "M"
        assert WeightLog.objects.filter(patient=patient).exists()
        assert result.still_missing["weight_log"] is False

    def test_sleep_log_created_with_existing_patient(self, user, conv_with_patient):
        conv, patient = conv_with_patient
        result = capture_from_message(conv.id, user.id, "Dormi 7 horas, qualidade 8")
        assert "sleep_log" in result.saved
        log = SleepLog.objects.get(patient=patient)
        assert float(log.duration_hours) == 7.0
        assert log.quality_score == 8

    def test_activity_log_created_with_existing_patient(self, user, conv_with_patient):
        conv, patient = conv_with_patient
        result = capture_from_message(conv.id, user.id, "Corri 30 minutos")
        assert "activity_log" in result.saved
        log = ActivityLog.objects.get(patient=patient)
        assert log.type == "corrida"
        assert log.duration_min == 30

    def test_nutrition_note_created_with_existing_patient(self, user, conv_with_patient):
        conv, patient = conv_with_patient
        result = capture_from_message(
            conv.id, user.id, "Almocei frango grelhado com arroz e salada"
        )
        assert "nutrition_note" in result.saved
        assert NutritionNote.objects.filter(patient=patient).exists()

    def test_no_patient_no_health_data_saved(self, user, conv):
        result = capture_from_message(
            conv.id, user.id, "Dormi 7 horas"
        )
        # Sem nome, sem patient → dados de saúde não persistidos
        assert result.patient_id is None
        assert WeightLog.objects.count() == 0
        assert SleepLog.objects.count() == 0

    def test_invalid_sleep_quality_not_saved(self, user, conv_with_patient):
        conv, patient = conv_with_patient
        result = capture_from_message(conv.id, user.id, "Dormi 7 horas, qualidade 15")
        assert "sleep_log" not in result.saved
        assert any(e["entity"] == "sleep_log" for e in result.errors)

    def test_non_health_message_no_op(self, user, conv):
        result = capture_from_message(conv.id, user.id, "Qual a capital da França?")
        assert result.saved == {}
        assert WeightLog.objects.count() == 0

    def test_dob_dedup_links_to_existing_patient(self, user, db):
        existing = Patient.objects.create(
            doctor=user,
            first_name="Ana",
            birth_date=date(1985, 5, 20),
            biological_sex="F",
        )
        # Nova conversa com paciente tentativo de mesmo nome/DOB
        conv = Conversation.objects.create(doctor=user, title="Nova conversa")
        # Captura nome → cria patient tentativo
        result1 = capture_from_message(conv.id, user.id, "Me chamo Ana")
        tentative_id = result1.patient_id
        assert tentative_id is not None
        assert tentative_id != existing.id

        # Captura DOB → deve fazer merge com o paciente existente
        result2 = capture_from_message(conv.id, user.id, "Nasci em 20/05/1985")
        conv.refresh_from_db()
        assert conv.patient_id == existing.id
        # Patient tentativo foi descartado
        assert not Patient.objects.filter(pk=tentative_id).exists()

    def test_llm_merge_when_enabled(self, user, conv, monkeypatch):
        monkeypatch.setenv("DATA_CAPTURE_LLM", "true")
        from apps.ai_engine.services.capture_models import ExtractedUserData, ExtractedWeight

        def fake_llm(text):
            return ExtractedUserData(
                name="Carlos",
                weight=ExtractedWeight(value_kg=82.5),
            )

        # Patch no namespace onde a referência foi importada
        monkeypatch.setattr(
            "apps.ai_engine.services.user_data_capture.extract_with_llm",
            fake_llm,
        )
        result = capture_from_message(conv.id, user.id, "Meu peso é 82,5 kg")
        assert result.patient_id is not None
        assert result.saved["weight_log"]["value_kg"] == 82.5

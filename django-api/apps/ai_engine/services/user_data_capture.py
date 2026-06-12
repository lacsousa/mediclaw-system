import logging

from django.utils import timezone
from rest_framework import serializers

from apps.ai_engine.skills.user_readiness import get_user_readiness
from apps.health_logs.services.persist import (
    DEFAULT_SLEEP_QUALITY,
    persist_activity_log,
    persist_nutrition_note,
    persist_sleep_log,
    persist_weight_log,
)
from apps.patients.services.patient import ensure_or_create_patient, resolve_patient_dob

from .capture_models import CaptureResult, ExtractedUserData
from .capture_rules import has_actionable_data, message_likely_has_health_data, parse_rules
from .data_extraction_llm import extract_with_llm, merge_extracted, _should_call_llm

logger = logging.getLogger(__name__)


def capture_from_message(
    conversation_id: int,
    doctor_id: int,
    text: str,
) -> CaptureResult:
    """
    Extrai e persiste dados de saúde/perfil do paciente a partir de uma mensagem de chat.
    Cria ou resolve o Patient vinculado à conversa conforme nome e DOB são capturados.
    """
    result = CaptureResult()

    if not message_likely_has_health_data(text):
        patient_id = _get_conversation_patient_id(conversation_id)
        result.patient_id = patient_id  # propaga sempre
        result.still_missing = get_user_readiness(patient_id).to_metadata()
        return result

    extracted = parse_rules(text)
    if _should_call_llm(text, extracted):
        llm_data = extract_with_llm(text)
        if llm_data:
            extracted = merge_extracted(extracted, llm_data)

    if not has_actionable_data(extracted):
        patient_id = _get_conversation_patient_id(conversation_id)
        result.patient_id = patient_id  # propaga sempre
        result.still_missing = get_user_readiness(patient_id).to_metadata()
        return result

    patient_id = _ensure_patient(conversation_id, doctor_id, extracted, result)
    # Se _ensure_patient não criou novo patient mas já havia um, propaga
    if result.patient_id is None and patient_id is not None:
        result.patient_id = patient_id

    _persist_health_data(patient_id, extracted, result)

    readiness = get_user_readiness(patient_id)
    result.still_missing = readiness.to_metadata()
    return result


def _get_conversation_patient_id(conversation_id: int) -> int | None:
    from apps.conversations.models import Conversation
    try:
        return Conversation.objects.get(pk=conversation_id).patient_id
    except Conversation.DoesNotExist:
        return None


def _ensure_patient(
    conversation_id: int,
    doctor_id: int,
    extracted: ExtractedUserData,
    result: CaptureResult,
) -> int | None:
    """
    Garante que existe um Patient vinculado à conversa, usando nome e/ou DOB extraídos.
    Retorna o patient_id resultante (pode ser None se nenhum nome foi capturado).
    """
    patient = None

    if extracted.name and extracted.name.strip():
        try:
            patient = ensure_or_create_patient(
                conversation_id=conversation_id,
                doctor_id=doctor_id,
                first_name=extracted.name.strip(),
            )
            result.saved["name"] = {"first_name": patient.first_name}
        except Exception as e:
            logger.warning("Erro ao criar/garantir paciente: %s", e)
            return _get_conversation_patient_id(conversation_id)

    # Se DOB foi capturada e já existe um patient na conversa, tentar dedup
    birth_date = extracted.profile.birth_date if extracted.profile else None
    if birth_date:
        current_patient_id = _get_conversation_patient_id(conversation_id)
        if current_patient_id is not None:
            try:
                patient = resolve_patient_dob(
                    conversation_id=conversation_id,
                    doctor_id=doctor_id,
                    birth_date=birth_date,
                )
            except Exception as e:
                logger.warning("Erro ao resolver DOB do paciente: %s", e)

    if patient is not None:
        result.patient_id = patient.id
        result.patient_created = getattr(result, "_patient_just_created", False)
        return patient.id

    return _get_conversation_patient_id(conversation_id)


def _persist_health_data(
    patient_id: int | None,
    data: ExtractedUserData,
    result: CaptureResult,
) -> None:
    """Persiste dados de saúde no paciente. Se patient_id for None, ignora silenciosamente."""
    if patient_id is None:
        return

    p = data.profile
    profile_payload = {}
    if p.birth_date:
        profile_payload["birth_date"] = p.birth_date.isoformat()
    if p.biological_sex:
        profile_payload["biological_sex"] = p.biological_sex
    if p.height_cm is not None:
        profile_payload["height_cm"] = p.height_cm
    if profile_payload:
        try:
            from apps.patients.models import Patient
            patient = Patient.objects.get(pk=patient_id)
            for field, value in profile_payload.items():
                setattr(patient, field, value)
            patient.save(update_fields=list(profile_payload.keys()) + ["updated_at"])
            result.saved["profile"] = profile_payload
        except serializers.ValidationError as e:
            result.errors.append({"entity": "profile", "detail": e.detail})

    if data.weight and data.weight.value_kg is not None:
        try:
            result.saved["weight_log"] = persist_weight_log(
                patient_id,
                {
                    "value_kg": data.weight.value_kg,
                    "measured_at": data.weight.measured_at or timezone.now(),
                },
            )
        except serializers.ValidationError as e:
            result.errors.append({"entity": "weight_log", "detail": e.detail})

    if data.sleep and data.sleep.duration_hours is not None:
        try:
            result.saved["sleep_log"] = persist_sleep_log(
                patient_id,
                {
                    "duration_hours": data.sleep.duration_hours,
                    "quality_score": data.sleep.quality_score or DEFAULT_SLEEP_QUALITY,
                    "started_at": data.sleep.started_at or timezone.now(),
                },
            )
        except serializers.ValidationError as e:
            result.errors.append({"entity": "sleep_log", "detail": e.detail})

    if data.activity and data.activity.duration_min is not None and data.activity.type:
        try:
            result.saved["activity_log"] = persist_activity_log(
                patient_id,
                {
                    "type": data.activity.type,
                    "duration_min": data.activity.duration_min,
                    "performed_at": data.activity.performed_at or timezone.now(),
                },
            )
        except serializers.ValidationError as e:
            result.errors.append({"entity": "activity_log", "detail": e.detail})

    if data.nutrition and data.nutrition.note:
        try:
            result.saved["nutrition_note"] = persist_nutrition_note(
                patient_id,
                {
                    "note": data.nutrition.note,
                    "logged_at": data.nutrition.logged_at or timezone.now(),
                },
            )
        except serializers.ValidationError as e:
            result.errors.append({"entity": "nutrition_note", "detail": e.detail})

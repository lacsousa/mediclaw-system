"""Criação e deduplicação de pacientes a partir de dados capturados no chat."""

from apps.common.logging_config import get_logger
from apps.patients.models import Patient
from apps.conversations.models import Conversation

logger = get_logger(__name__)


def ensure_or_create_patient(
    conversation_id: int,
    doctor_id: int,
    first_name: str,
) -> Patient:
    """
    Cria um Patient tentativo para a conversa, se ainda não houver um vinculado.
    Cada conversa cria seu próprio Patient (dedup por nome+DOB ocorre em resolve_patient_dob).
    Atualiza conversation.patient e salva.
    """
    conv = Conversation.objects.get(pk=conversation_id)

    if conv.patient_id is not None:
        # Já tem paciente — apenas atualiza o nome se ainda não estava preenchido
        patient = conv.patient
        if not patient.first_name:
            patient.first_name = first_name.strip()
            patient.save(update_fields=["first_name", "updated_at"])
        return patient

    patient = Patient.objects.create(
        doctor_id=doctor_id,
        first_name=first_name.strip(),
    )
    conv.patient = patient
    conv.title = first_name.strip()[:120]
    conv.save(update_fields=["patient", "title", "updated_at"])
    logger.debug(
        "patient_created",
        patient_id=patient.id,
        conversation_id=conversation_id,
    )
    return patient


def resolve_patient_dob(
    conversation_id: int, doctor_id: int, birth_date
) -> Patient | None:
    """
    Ao capturar a data de nascimento, verifica se já existe um Patient com
    mesmo nome + DOB para este médico. Se sim, re-vincula a conversa ao Patient
    existente e deleta o tentativo (se for diferente e não tiver outros dados).
    """
    conv = Conversation.objects.get(pk=conversation_id)
    if conv.patient_id is None:
        return None

    current_patient = conv.patient

    existing = (
        Patient.objects.filter(
            doctor_id=doctor_id,
            first_name__iexact=current_patient.first_name,
            birth_date=birth_date,
        )
        .exclude(pk=current_patient.pk)
        .first()
    )

    if existing:
        # Reutiliza paciente existente — descarta o tentativo sem dados
        _tentative_has_no_data = not (
            current_patient.weight_logs.exists()
            or current_patient.sleep_logs.exists()
            or current_patient.activity_logs.exists()
            or current_patient.nutrition_notes.exists()
        )
        conv.patient = existing
        conv.title = existing.first_name[:120]
        conv.save(update_fields=["patient", "title", "updated_at"])

        if _tentative_has_no_data:
            current_patient.delete()
            logger.debug(
                "patient_merged",
                tentative_patient_id=current_patient.id,
                existing_patient_id=existing.id,
                conversation_id=conversation_id,
            )
        return existing

    # Nenhum match — atualiza DOB no paciente tentativo
    current_patient.birth_date = birth_date
    current_patient.save(update_fields=["birth_date", "updated_at"])
    return current_patient

from dataclasses import dataclass

from apps.health_logs.models import WeightLog

REQUIRED_PROFILE_FIELDS = ("birth_date", "biological_sex", "height_cm")

PROFILE_FIELD_LABELS = {
    "birth_date": "data de nascimento",
    "biological_sex": "sexo biológico",
    "height_cm": "altura (cm)",
}


@dataclass
class UserReadiness:
    is_complete: bool
    missing_name: bool
    missing_profile_fields: list[str]
    missing_weight_log: bool

    def missing_labels_pt(self) -> list[str]:
        labels = []
        if self.missing_name:
            labels.append("nome")
        labels.extend(
            PROFILE_FIELD_LABELS[f]
            for f in self.missing_profile_fields
            if f in PROFILE_FIELD_LABELS
        )
        if self.missing_weight_log:
            labels.append("peso atual (kg)")
        return labels

    def to_metadata(self) -> dict:
        return {
            "name": self.missing_name,
            "profile": list(self.missing_profile_fields),
            "weight_log": self.missing_weight_log,
        }


def get_user_readiness(patient_id: int | None) -> UserReadiness:
    """
    Avalia o grau de completude dos dados do paciente.
    patient_id=None → todos os campos faltando (conversa sem paciente identificado).
    """
    if patient_id is None:
        return UserReadiness(
            is_complete=False,
            missing_name=True,
            missing_profile_fields=list(REQUIRED_PROFILE_FIELDS),
            missing_weight_log=True,
        )

    from apps.patients.models import Patient

    try:
        patient = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return UserReadiness(
            is_complete=False,
            missing_name=True,
            missing_profile_fields=list(REQUIRED_PROFILE_FIELDS),
            missing_weight_log=True,
        )

    missing_name = not (patient.first_name or "").strip()
    missing_profile = [
        f for f in REQUIRED_PROFILE_FIELDS if not getattr(patient, f, None)
    ]
    missing_weight = not WeightLog.objects.filter(patient_id=patient_id).exists()

    return UserReadiness(
        is_complete=not missing_name and not missing_profile and not missing_weight,
        missing_name=missing_name,
        missing_profile_fields=missing_profile,
        missing_weight_log=missing_weight,
    )

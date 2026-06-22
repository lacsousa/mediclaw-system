import json
import logging
import os

from pydantic import ValidationError

from .capture_models import (
    ExtractedActivity,
    ExtractedNutrition,
    ExtractedProfile,
    ExtractedSleep,
    ExtractedUserData,
    ExtractedWeight,
)
from .capture_rules import has_actionable_data, message_likely_has_health_data

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM = """Você extrai dados de saúde do PACIENTE a partir da mensagem do MÉDICO em português.
O médico descreve o paciente em terceira pessoa ou formato de prontuário (ex.: "Paciente Maria Silva, 72 kg, 1,65 m").
Responda APENAS com um objeto JSON válido, sem markdown, com esta estrutura (use null quando ausente):
{
  "name": "string ou null",
  "profile": {
    "birth_date": "YYYY-MM-DD ou null",
    "biological_sex": "M|F|OTHER ou null",
    "height_cm": número ou null
  },
  "weight": { "value_kg": número ou null, "measured_at": "ISO8601 ou null" },
  "sleep": {
    "duration_hours": número ou null,
    "quality_score": 1-10 ou null,
    "started_at": "ISO8601 ou null"
  },
  "activity": {
    "type": "string curta ou null",
    "duration_min": inteiro ou null,
    "performed_at": "ISO8601 ou null"
  },
  "nutrition": { "note": "texto da refeição ou null", "logged_at": "ISO8601 ou null" }
}
Não invente dados. Extraia somente o que foi explicitamente informado nesta mensagem sobre o paciente."""


def _llm_enabled() -> bool:
    return os.environ.get("DATA_CAPTURE_LLM", "true").lower() in ("1", "true", "yes")


def _should_call_llm(text: str, rules_data: ExtractedUserData) -> bool:
    if not _llm_enabled():
        return False
    if not message_likely_has_health_data(text):
        return False
    return len(text.strip()) >= 5 or has_actionable_data(rules_data)


def extract_with_llm(text: str) -> ExtractedUserData | None:
    from apps.ai_engine.providers import get_provider

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM},
        {"role": "user", "content": text},
    ]
    try:
        provider = get_provider()
        raw = provider.complete_json(messages, max_tokens=400)
        payload = json.loads(raw)
        return ExtractedUserData.model_validate(payload)
    except (ValidationError, json.JSONDecodeError, AttributeError, Exception) as e:
        logger.warning("LLM data extraction failed: %s", e)
        return None


def merge_extracted(
    primary: ExtractedUserData, secondary: ExtractedUserData
) -> ExtractedUserData:
    """Rules (primary) win; secondary (LLM) fills null gaps only."""
    p1, p2 = primary.profile, secondary.profile
    profile = ExtractedProfile(
        birth_date=p1.birth_date or p2.birth_date,
        biological_sex=p1.biological_sex or p2.biological_sex,
        height_cm=p1.height_cm or p2.height_cm,
    )

    def _opt_weight() -> ExtractedWeight | None:
        w1, w2 = primary.weight, secondary.weight
        if not w1 and not w2:
            return None
        w1 = w1 or ExtractedWeight()
        w2 = w2 or ExtractedWeight()
        if w1.value_kg is None and w2.value_kg is None:
            return None
        return ExtractedWeight(
            value_kg=w1.value_kg if w1.value_kg is not None else w2.value_kg,
            measured_at=w1.measured_at or w2.measured_at,
        )

    def _opt_sleep() -> ExtractedSleep | None:
        s1, s2 = primary.sleep, secondary.sleep
        if not s1 and not s2:
            return None
        s1 = s1 or ExtractedSleep()
        s2 = s2 or ExtractedSleep()
        if s1.duration_hours is None and s2.duration_hours is None:
            return None
        return ExtractedSleep(
            duration_hours=(
                s1.duration_hours
                if s1.duration_hours is not None
                else s2.duration_hours
            ),
            quality_score=(
                s1.quality_score if s1.quality_score is not None else s2.quality_score
            ),
            started_at=s1.started_at or s2.started_at,
        )

    def _opt_activity() -> ExtractedActivity | None:
        a1, a2 = primary.activity, secondary.activity
        if not a1 and not a2:
            return None
        a1 = a1 or ExtractedActivity()
        a2 = a2 or ExtractedActivity()
        dur = a1.duration_min if a1.duration_min is not None else a2.duration_min
        typ = a1.type or a2.type
        if not dur or not typ:
            return None
        return ExtractedActivity(
            type=typ,
            duration_min=dur,
            performed_at=a1.performed_at or a2.performed_at,
        )

    def _opt_nutrition() -> ExtractedNutrition | None:
        n1, n2 = primary.nutrition, secondary.nutrition
        if not n1 and not n2:
            return None
        note = (n1.note if n1 and n1.note else None) or (n2.note if n2 else None)
        if not note:
            return None
        return ExtractedNutrition(
            note=note,
            logged_at=(n1.logged_at if n1 else None) or (n2.logged_at if n2 else None),
        )

    name = primary.name or (secondary.name if secondary else None)

    return ExtractedUserData(
        name=name.strip() if name else None,
        profile=profile,
        weight=_opt_weight(),
        sleep=_opt_sleep(),
        activity=_opt_activity(),
        nutrition=_opt_nutrition(),
    )

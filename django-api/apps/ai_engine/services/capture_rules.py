import re
from datetime import date, datetime
from typing import Literal

from django.utils import timezone

from .capture_models import (
    ExtractedActivity,
    ExtractedNutrition,
    ExtractedProfile,
    ExtractedSleep,
    ExtractedUserData,
    ExtractedWeight,
)

_WEIGHT_KG_RE = re.compile(
    r"(?:peso\s*[:\s]*)?(\d{1,3}(?:[.,]\d{1,2})?)\s*kg\b",
    re.IGNORECASE,
)
_HEIGHT_CM_RE = re.compile(
    r"(?:altura\s*[:\s]*)?(\d{2,3})\s*cm\b|(\d[.,]\d{1,2})\s*m\b",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
_SEX_RE = re.compile(
    r"\b(homem|masculino|mulher|feminino|sexo\s*[:\s]*(m|f|other|outro))\b",
    re.IGNORECASE,
)
_SLEEP_HOURS_RE = re.compile(
    r"(?:dormi|sono|dormiu|dormidas?)\s*(?:de\s*)?(\d{1,2}(?:[.,]\d)?)\s*(?:h|horas?)\b",
    re.IGNORECASE,
)
_SLEEP_HOURS_ALT_RE = re.compile(
    r"\b(\d{1,2}(?:[.,]\d)?)\s*(?:h|horas?)\s*(?:de\s*)?sono\b",
    re.IGNORECASE,
)
_SLEEP_QUALITY_RE = re.compile(
    r"qualidade\s*(?:do\s*sono\s*)?[:\s]*(\d{1,2})(?:\s*/\s*10)?",
    re.IGNORECASE,
)
_ACTIVITY_VERBS = (
    r"corr(?:i|ida)|caminh(?:ei|ada)|muscula[cç][aã]o|nata[cç][aã]o|ciclismo|"
    r"yoga|crossfit|treino|academia"
)
_ACTIVITY_RE = re.compile(
    rf"\b({_ACTIVITY_VERBS})\b[^.]{{0,40}}?(\d{{1,4}})\s*(?:min(?:utos?)?|min)\b",
    re.IGNORECASE,
)
_ACTIVITY_ALT_RE = re.compile(
    rf"\b(\d{{1,4}})\s*(?:min(?:utos?)?|min)\s*(?:de\s*)?({_ACTIVITY_VERBS})\b",
    re.IGNORECASE,
)
_NUTRITION_TRIGGERS = re.compile(
    r"\b(almocei|jantei|caf[eé]\s*da\s*manh[aã]|lanchei|comi|refei[cç][aã]o)\b",
    re.IGNORECASE,
)
_NAME_RE = re.compile(
    r"(?:meu\s+nome\s+[ée]\s+|me\s+chamo\s+|sou\s+(?:o|a)\s+|paciente[:\s]+)"
    r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s'\-]{0,118}[A-Za-zÀ-ÿ])",
    re.IGNORECASE,
)

_ACTIVITY_TYPE_MAP = {
    "corrida": "corrida",
    "corri": "corrida",
    "caminhada": "caminhada",
    "caminhei": "caminhada",
    "musculação": "musculação",
    "musculacao": "musculação",
    "natação": "natação",
    "natacao": "natação",
    "ciclismo": "ciclismo",
    "yoga": "yoga",
    "crossfit": "crossfit",
    "treino": "treino",
    "academia": "academia",
}


def _parse_float(s: str) -> float:
    return float(s.replace(",", "."))


def _parse_date(d: str, m: str, y: str) -> date | None:
    try:
        year = int(y)
        if year < 100:
            year += 1900 if year > 30 else 2000
        return date(year, int(m), int(d))
    except ValueError:
        return None


def _parse_sex(text: str) -> Literal["M", "F", "OTHER"] | None:
    m = _SEX_RE.search(text)
    if not m:
        return None
    token = m.group(1).lower() if m.lastindex == 1 else m.group(0).lower()
    if "homem" in token or "masculino" in token or token.strip() == "m":
        return "M"
    if "mulher" in token or "feminino" in token or token.strip() == "f":
        return "F"
    if "outro" in token or "other" in token:
        return "OTHER"
    return None


def parse_rules(text: str) -> ExtractedUserData:
    name: str | None = None
    profile = ExtractedProfile()
    weight: ExtractedWeight | None = None
    sleep: ExtractedSleep | None = None
    activity: ExtractedActivity | None = None
    nutrition: ExtractedNutrition | None = None

    wm = _WEIGHT_KG_RE.search(text)
    if wm:
        weight = ExtractedWeight(value_kg=_parse_float(wm.group(1)))

    hm = _HEIGHT_CM_RE.search(text)
    if hm:
        if hm.group(1):
            profile.height_cm = int(hm.group(1))
        elif hm.group(2):
            profile.height_cm = int(round(_parse_float(hm.group(2)) * 100))

    dm = _DATE_RE.search(text)
    if dm:
        profile.birth_date = _parse_date(dm.group(1), dm.group(2), dm.group(3))

    sex = _parse_sex(text)
    if sex:
        profile.biological_sex = sex

    sh = _SLEEP_HOURS_RE.search(text) or _SLEEP_HOURS_ALT_RE.search(text)
    if sh:
        sleep = ExtractedSleep(duration_hours=_parse_float(sh.group(1)))
        sq = _SLEEP_QUALITY_RE.search(text)
        if sq:
            sleep.quality_score = int(sq.group(1))

    am = _ACTIVITY_RE.search(text) or _ACTIVITY_ALT_RE.search(text)
    if am:
        groups = am.groups()
        if len(groups) >= 2:
            if groups[0].isdigit():
                duration_min, raw_type = int(groups[0]), groups[1]
            else:
                raw_type, duration_min = groups[0], int(groups[1])
            act_type = _ACTIVITY_TYPE_MAP.get(raw_type.lower(), raw_type.lower())
            activity = ExtractedActivity(type=act_type, duration_min=duration_min)

    if _NUTRITION_TRIGGERS.search(text):
        trigger = _NUTRITION_TRIGGERS.search(text)
        if trigger:
            start = trigger.start()
            note = text[start:].strip()
            if len(note) >= 10:
                nutrition = ExtractedNutrition(note=note[:1000])

    nm = _NAME_RE.search(text)
    if nm:
        name = nm.group(1).strip()

    return ExtractedUserData(
        name=name,
        profile=profile,
        weight=weight,
        sleep=sleep,
        activity=activity,
        nutrition=nutrition,
    )


def has_actionable_data(data: ExtractedUserData) -> bool:
    if data.name and data.name.strip():
        return True
    p = data.profile
    if p.birth_date or p.biological_sex or p.height_cm:
        return True
    if data.weight and data.weight.value_kg is not None:
        return True
    if data.sleep and data.sleep.duration_hours is not None:
        return True
    if data.activity and data.activity.duration_min and data.activity.type:
        return True
    if data.nutrition and data.nutrition.note:
        return True
    return False


def message_likely_has_health_data(text: str) -> bool:
    if len(text.strip()) < 8:
        return False
    keywords = (
        "kg",
        "cm",
        "peso",
        "altura",
        "dormi",
        "sono",
        "corri",
        "min",
        "almocei",
        "jantei",
        "nasci",
        "homem",
        "mulher",
        "horas",
        "nome",
        "chamo",
        "me chamo",
        # dados de paciente (contexto médico)
        "paciente",
        "anos",
        "ano",
        "idade",
        "sexo",
        "feminino",
        "masculino",
        "sou",
    )
    lower = text.lower()
    return any(k in lower for k in keywords)

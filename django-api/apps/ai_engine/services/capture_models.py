from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedProfile(BaseModel):
    birth_date: date | None = None
    biological_sex: Literal["M", "F", "OTHER"] | None = None
    height_cm: int | None = None


class ExtractedWeight(BaseModel):
    value_kg: float | None = None
    measured_at: datetime | None = None


class ExtractedSleep(BaseModel):
    duration_hours: float | None = None
    quality_score: int | None = None
    started_at: datetime | None = None


class ExtractedActivity(BaseModel):
    type: str | None = None
    duration_min: int | None = None
    performed_at: datetime | None = None


class ExtractedNutrition(BaseModel):
    note: str | None = None
    logged_at: datetime | None = None


class ExtractedUserData(BaseModel):
    name: str | None = None
    profile: ExtractedProfile = Field(default_factory=ExtractedProfile)
    weight: ExtractedWeight | None = None
    sleep: ExtractedSleep | None = None
    activity: ExtractedActivity | None = None
    nutrition: ExtractedNutrition | None = None


def _json_safe(value):
    """Converte date/datetime aninhados para strings ISO (JSONField / SSE)."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


class CaptureResult(BaseModel):
    saved: dict = Field(default_factory=dict)
    errors: list[dict] = Field(default_factory=list)
    still_missing: dict = Field(default_factory=dict)
    patient_id: int | None = None
    patient_created: bool = False

    def to_metadata(self) -> dict:
        return _json_safe(
            {
                "saved": self.saved,
                "errors": self.errors,
                "still_missing": self.still_missing,
            }
        )

    def saved_summary_pt(self) -> str:
        lines = []
        if "name" in self.saved:
            lines.append(f"Nome: {self.saved['name'].get('first_name', '')}")
        if "profile" in self.saved:
            parts = []
            p = self.saved["profile"]
            if p.get("birth_date"):
                parts.append(f"data de nascimento: {p['birth_date']}")
            if p.get("biological_sex"):
                parts.append(f"sexo biológico: {p['biological_sex']}")
            if p.get("height_cm"):
                parts.append(f"altura: {p['height_cm']} cm")
            if parts:
                lines.append("Perfil: " + ", ".join(parts))
        if "weight_log" in self.saved:
            w = self.saved["weight_log"]
            lines.append(f"Peso: {w.get('value_kg')} kg")
        if "sleep_log" in self.saved:
            s = self.saved["sleep_log"]
            lines.append(
                f"Sono: {s.get('duration_hours')} h, qualidade {s.get('quality_score')}/10"
            )
        if "activity_log" in self.saved:
            a = self.saved["activity_log"]
            lines.append(f"Atividade ({a.get('type')}): {a.get('duration_min')} min")
        if "nutrition_note" in self.saved:
            n = self.saved["nutrition_note"]
            note = (n.get("note") or "")[:80]
            lines.append(f"Alimentação registrada: {note}")
        return "\n".join(lines) if lines else ""

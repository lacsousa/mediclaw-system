from apps.health_logs.services.aggregate import summarize


def health_summary(patient_id: int | None, window: int = 7) -> dict:
    if patient_id is None:
        return {
            "window_days": window,
            "avg_sleep_hours": None,
            "avg_sleep_quality": None,
            "latest_weight_kg": None,
            "weight_trend_kg": None,
            "total_activity_min": 0,
            "last_nutrition_notes": [],
        }
    return summarize(patient_id, window)

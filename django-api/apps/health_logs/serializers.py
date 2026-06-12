from django.utils import timezone
from rest_framework import serializers

from .models import ActivityLog, NutritionNote, SleepLog, WeightLog


class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ["id", "value_kg", "measured_at"]
        read_only_fields = ["id"]

    def validate_value_kg(self, v):
        if not (20 <= float(v) <= 400):
            raise serializers.ValidationError(
                "Peso fora do intervalo plausível (20–400 kg)."
            )
        return v

    def validate_measured_at(self, v):
        if v > timezone.now():
            raise serializers.ValidationError("measured_at não pode ser no futuro.")
        return v


class SleepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepLog
        fields = ["id", "duration_hours", "quality_score", "started_at"]
        read_only_fields = ["id"]

    def validate_quality_score(self, v):
        if not (1 <= v <= 10):
            raise serializers.ValidationError("quality_score deve estar entre 1 e 10.")
        return v


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ["id", "type", "duration_min", "performed_at"]
        read_only_fields = ["id"]

    def validate_duration_min(self, v):
        if v < 1:
            raise serializers.ValidationError("duration_min deve ser ≥ 1.")
        return v


class NutritionNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionNote
        fields = ["id", "note", "logged_at"]
        read_only_fields = ["id"]

    def validate_note(self, v):
        if len(v) > 1000:
            raise serializers.ValidationError("note excede 1000 caracteres.")
        return v

from rest_framework import serializers

from .models import Patient


class PatientListSerializer(serializers.ModelSerializer):
    conversation_count = serializers.IntegerField(read_only=True, default=0)
    last_seen_at = serializers.DateTimeField(read_only=True, default=None)
    latest_weight_kg = serializers.DecimalField(
        read_only=True, max_digits=5, decimal_places=2, default=None
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "first_name",
            "birth_date",
            "biological_sex",
            "height_cm",
            "conversation_count",
            "last_seen_at",
            "latest_weight_kg",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ConversationSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class WeightLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value_kg = serializers.DecimalField(max_digits=5, decimal_places=2)
    measured_at = serializers.DateTimeField()


class SleepLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    duration_hours = serializers.DecimalField(max_digits=4, decimal_places=2)
    quality_score = serializers.IntegerField()
    started_at = serializers.DateTimeField()


class ActivityLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    duration_min = serializers.IntegerField()
    performed_at = serializers.DateTimeField()


class NutritionNoteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    note = serializers.CharField()
    logged_at = serializers.DateTimeField()


class PatientDetailSerializer(PatientListSerializer):
    weight_logs = WeightLogSerializer(many=True, read_only=True)
    sleep_logs = SleepLogSerializer(many=True, read_only=True)
    activity_logs = ActivityLogSerializer(many=True, read_only=True)
    nutrition_notes = NutritionNoteSerializer(many=True, read_only=True)
    conversations = serializers.SerializerMethodField()

    class Meta(PatientListSerializer.Meta):
        fields = PatientListSerializer.Meta.fields + [
            "weight_logs",
            "sleep_logs",
            "activity_logs",
            "nutrition_notes",
            "conversations",
        ]

    def get_conversations(self, obj):
        convs = obj.conversations.order_by("-updated_at")
        return ConversationSummarySerializer(convs, many=True).data

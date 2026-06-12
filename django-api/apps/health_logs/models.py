from django.db import models


class WeightLog(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="weight_logs",
    )
    value_kg = models.DecimalField(max_digits=5, decimal_places=2)
    measured_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["patient", "-measured_at"])]
        ordering = ["-measured_at"]


class SleepLog(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="sleep_logs",
    )
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    quality_score = models.PositiveSmallIntegerField()
    started_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["patient", "-started_at"])]
        ordering = ["-started_at"]


class ActivityLog(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    type = models.CharField(max_length=40)
    duration_min = models.PositiveSmallIntegerField()
    performed_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["patient", "-performed_at"])]
        ordering = ["-performed_at"]


class NutritionNote(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="nutrition_notes",
    )
    note = models.TextField()
    logged_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["patient", "-logged_at"])]
        ordering = ["-logged_at"]

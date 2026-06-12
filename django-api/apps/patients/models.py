from django.conf import settings
from django.db import models


SEX_CHOICES = [("M", "M"), ("F", "F"), ("OTHER", "OTHER")]


class Patient(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patients",
    )
    first_name = models.CharField(max_length=120)
    birth_date = models.DateField(null=True, blank=True)
    biological_sex = models.CharField(
        max_length=10, choices=SEX_CHOICES, null=True, blank=True
    )
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "first_name", "birth_date"],
                condition=models.Q(birth_date__isnull=False),
                name="unique_patient_name_dob_per_doctor",
            )
        ]
        indexes = [
            models.Index(fields=["doctor", "first_name"]),
            models.Index(fields=["doctor", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} (dr: {self.doctor_id})"

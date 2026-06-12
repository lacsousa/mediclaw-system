from django.conf import settings
from django.db import models


class ActiveConversationManager(models.Manager):
    """Exclui conversas soft-deletadas por padrão."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Conversation(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    title = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveConversationManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["doctor", "-updated_at"]),
            models.Index(fields=["patient", "-updated_at"]),
        ]


class Message(models.Model):
    ROLE_CHOICES = [("USER", "USER"), ("ASSISTANT", "ASSISTANT"), ("SYSTEM", "SYSTEM")]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    blocked_by_guardrail = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

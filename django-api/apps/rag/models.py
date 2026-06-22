from django.conf import settings
from django.db import models


class KnowledgeDocument(models.Model):
    STATUS_CHOICES = [
        ("PROCESSING", "Processing"),
        ("INDEXED", "Indexed"),
        ("ERROR", "Error"),
    ]

    title = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=80)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default="PROCESSING"
    )
    chunk_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="knowledge_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"

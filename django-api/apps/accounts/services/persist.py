"""Persistência de dados de conta sem request HTTP (captura via chat)."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


def persist_user_name(user_id: int, name: str) -> dict:
    cleaned = (name or "").strip()
    if len(cleaned) < 2:
        raise serializers.ValidationError("Nome deve ter pelo menos 2 caracteres.")
    if len(cleaned) > 120:
        raise serializers.ValidationError("Nome não pode exceder 120 caracteres.")
    user = User.objects.get(pk=user_id)
    user.first_name = cleaned
    user.save(update_fields=["first_name"])
    return {"first_name": cleaned}

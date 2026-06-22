import re
from django.utils import timezone
from rest_framework import serializers
from .models import User

PASSWORD_RX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=120)
    accept_terms = serializers.BooleanField()

    def validate_password(self, v):
        if not PASSWORD_RX.match(v):
            raise serializers.ValidationError(
                "Senha deve ter ≥ 8 chars, com letra e dígito."
            )
        return v

    def validate_accept_terms(self, v):
        if not v:
            raise serializers.ValidationError("Aceite dos termos é obrigatório.")
        return v

    def validate_email(self, v):
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return v.lower()

    def create(self, validated):
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            first_name=validated["name"],
            accepted_terms_at=timezone.now(),
        )
        from apps.conversations.services.welcome import ensure_welcome_conversation

        ensure_welcome_conversation(user)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "role", "accepted_terms_at"]


class MeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)

    def validate_email(self, value):
        email = value.lower()
        user = self.context["user"]
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return email


class AdminCreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=120)
    role = serializers.ChoiceField(choices=["USER", "ADMIN"], default="USER")

    def validate_password(self, v):
        if not PASSWORD_RX.match(v):
            raise serializers.ValidationError(
                "Senha deve ter ≥ 8 chars, com letra e dígito."
            )
        return v

    def validate_email(self, v):
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return v.lower()

    def create(self, validated):
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            first_name=validated["name"],
            role=validated.get("role", "USER"),
        )
        from apps.conversations.services.welcome import ensure_welcome_conversation

        ensure_welcome_conversation(user)
        return user

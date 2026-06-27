# Epic 2 — Auth & Users

> **Plano-MVP Etapa 1.** Modelo de usuário customizado, JWT, consentimento LGPD.
> Referência: [PRD §EPIC-02](../PRD.md) · [TASKS §Epic 2](../TASKS.md#epic-2--auth--users)

---

## Objetivo

Autenticação JWT robusta com modelo de usuário customizado por e-mail, perfil opcional para personalização da IA e registro de aceite dos termos (LGPD).

## Dependências

- Epic 1 concluído (settings, common, DRF configurado)

---

## Modelos

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("E-mail obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", "ADMIN")
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    ROLE_CHOICES = [("USER", "USER"), ("ADMIN", "ADMIN")]
    username = models.CharField(max_length=150, blank=True)  # tornado opcional
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="USER")
    accepted_terms_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


class Profile(models.Model):
    SEX_CHOICES = [("M", "M"), ("F", "F"), ("OTHER", "OTHER")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    birth_date = models.DateField(null=True, blank=True)
    biological_sex = models.CharField(max_length=10, choices=SEX_CHOICES, null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
```

`config/settings.py`:
```python
AUTH_USER_MODEL = "accounts.User"
```

---

## Serializers

```python
# apps/accounts/serializers.py
import re
from django.utils import timezone
from rest_framework import serializers
from .models import User, Profile

PASSWORD_RX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["birth_date", "biological_sex", "height_cm"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=120)
    accept_terms = serializers.BooleanField()

    def validate_password(self, v):
        if not PASSWORD_RX.match(v):
            raise serializers.ValidationError("Senha deve ter ≥ 8 chars, com letra e dígito.")
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
        Profile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "role", "accepted_terms_at", "profile"]
```

---

## Views

```python
# apps/accounts/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer
from apps.audit.services.log import record
from apps.common.exceptions import AppError


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    refresh = RefreshToken.for_user(user)
    record("USER_REGISTERED", user=user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = (request.data.get("email") or "").lower()
    password = request.data.get("password") or ""
    user = authenticate(request, username=email, password=password)
    if not user or not user.is_active:
        raise AppError("INVALID_CREDENTIALS", "E-mail ou senha incorretos.", 401)
    refresh = RefreshToken.for_user(user)
    record("LOGIN", user=user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    })


@api_view(["GET", "PATCH"])
def me(request):
    user = request.user
    if request.method == "GET":
        return Response(UserSerializer(user).data)
    name = request.data.get("name")
    if name is not None:
        user.first_name = name
        user.save(update_fields=["first_name"])
    profile_data = request.data.get("profile") or {}
    if profile_data:
        ps = ProfileSerializer(user.profile, data=profile_data, partial=True)
        ps.is_valid(raise_exception=True)
        ps.save()
    return Response(UserSerializer(user).data)
```

```python
# apps/accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register, login, me

urlpatterns = [
    path("register", register),
    path("login", login),
    path("refresh", TokenRefreshView.as_view()),
    path("me", me),
]
```

---

## Permissions

```python
# apps/common/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None) or getattr(obj, "uploaded_by", None)
        return owner == request.user
```

---

## Critérios de Aceite (resumo do PRD)

- [ ] Cadastro/login retornam `{access, refresh, user}` no envelope
- [ ] Senha sempre persistida via `set_password`
- [ ] `accept_terms=false` ou ausente → 400
- [ ] `EMAIL_ALREADY_EXISTS` em duplicidade
- [ ] `/me` GET sem dados sensíveis; PATCH atualiza nome e profile
- [ ] 401 sem token; 403 com role insuficiente
- [ ] Throttle aplicado às rotas anônimas

---

## Testes obrigatórios

```python
# tests/accounts/test_auth.py
def test_register_creates_user_and_returns_tokens(api_client, db): ...
def test_register_rejects_weak_password(api_client, db): ...
def test_register_blocks_without_accept_terms(api_client, db): ...
def test_login_with_wrong_password_returns_401(api_client, user): ...
def test_login_inactive_user_returns_401(api_client, user): ...
def test_me_requires_auth(api_client): ...
def test_me_patch_updates_profile(auth_client): ...
```

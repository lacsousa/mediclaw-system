# Epic 3 — Core API: Health Logs

> **Plano-MVP Etapa 2.** CRUD de dados biométricos e service de agregação que alimenta a IA.
> Referência: [PRD §EPIC-03](../PRD.md) · [TASKS §Epic 3](../TASKS.md#epic-3--health-logs-core-api)

---

## Objetivo

Persistir, consultar e agregar dados biométricos do usuário. O service de agregação (`summarize`) é a interface usada pelo `ai_engine` para compor o contexto do prompt — portanto, deve ser estável e testado.

## Dependências

- E2 concluído (`User` e auth funcionando)

---

## Modelos

```python
# apps/health_logs/models.py
from django.db import models
from django.conf import settings

class WeightLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weight_logs")
    value_kg = models.DecimalField(max_digits=5, decimal_places=2)
    measured_at = models.DateTimeField()
    class Meta:
        indexes = [models.Index(fields=["user", "-measured_at"])]
        ordering = ["-measured_at"]


class SleepLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sleep_logs")
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    quality_score = models.PositiveSmallIntegerField()  # 1-10
    started_at = models.DateTimeField()
    class Meta:
        indexes = [models.Index(fields=["user", "-started_at"])]
        ordering = ["-started_at"]


class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs")
    type = models.CharField(max_length=40)
    duration_min = models.PositiveSmallIntegerField()
    performed_at = models.DateTimeField()
    class Meta:
        indexes = [models.Index(fields=["user", "-performed_at"])]
        ordering = ["-performed_at"]


class NutritionNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="nutrition_notes")
    note = models.TextField()
    logged_at = models.DateTimeField()
    class Meta:
        indexes = [models.Index(fields=["user", "-logged_at"])]
        ordering = ["-logged_at"]
```

> **Nota:** o nome do modelo `ActivityLog` aqui (atividade física) coexiste com `apps.audit.ActivityLog` (auditoria). Importar sempre com namespace explícito (`from apps.health_logs.models import ActivityLog as PhysicalActivityLog` se houver colisão real em algum módulo).

---

## Serializers

```python
# apps/health_logs/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import WeightLog, SleepLog, ActivityLog, NutritionNote

class _BaseOwnedSerializer(serializers.ModelSerializer):
    def create(self, validated):
        validated["user"] = self.context["request"].user
        return super().create(validated)


class WeightLogSerializer(_BaseOwnedSerializer):
    class Meta:
        model = WeightLog
        fields = ["id", "value_kg", "measured_at"]

    def validate_value_kg(self, v):
        if not (20 <= float(v) <= 400):
            raise serializers.ValidationError("Peso fora do intervalo plausível (20–400 kg).")
        return v

    def validate_measured_at(self, v):
        if v > timezone.now():
            raise serializers.ValidationError("measured_at não pode ser no futuro.")
        return v


class SleepLogSerializer(_BaseOwnedSerializer):
    class Meta:
        model = SleepLog
        fields = ["id", "duration_hours", "quality_score", "started_at"]

    def validate_quality_score(self, v):
        if not (1 <= v <= 10):
            raise serializers.ValidationError("quality_score deve estar entre 1 e 10.")
        return v


class ActivityLogSerializer(_BaseOwnedSerializer):
    class Meta:
        model = ActivityLog
        fields = ["id", "type", "duration_min", "performed_at"]

    def validate_duration_min(self, v):
        if v < 1:
            raise serializers.ValidationError("duration_min deve ser ≥ 1.")
        return v


class NutritionNoteSerializer(_BaseOwnedSerializer):
    class Meta:
        model = NutritionNote
        fields = ["id", "note", "logged_at"]

    def validate_note(self, v):
        if len(v) > 1000:
            raise serializers.ValidationError("note excede 1000 caracteres.")
        return v
```

---

## ViewSets

```python
# apps/health_logs/views.py
from rest_framework import viewsets, mixins
from .models import WeightLog, SleepLog, ActivityLog, NutritionNote
from .serializers import (
    WeightLogSerializer, SleepLogSerializer, ActivityLogSerializer, NutritionNoteSerializer
)
from .services.aggregate import summarize
from rest_framework.decorators import api_view
from rest_framework.response import Response


class _OwnedQuerysetMixin:
    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        from_ = self.request.query_params.get("from")
        to_ = self.request.query_params.get("to")
        ts_field = self.timestamp_field
        if from_:
            qs = qs.filter(**{f"{ts_field}__gte": from_})
        if to_:
            qs = qs.filter(**{f"{ts_field}__lte": to_})
        return qs


class WeightLogViewSet(_OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = WeightLog.objects.all()
    serializer_class = WeightLogSerializer
    timestamp_field = "measured_at"
    http_method_names = ["get", "post", "delete"]


class SleepLogViewSet(_OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = SleepLog.objects.all()
    serializer_class = SleepLogSerializer
    timestamp_field = "started_at"
    http_method_names = ["get", "post", "delete"]


class ActivityLogViewSet(_OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    timestamp_field = "performed_at"
    http_method_names = ["get", "post", "delete"]


class NutritionNoteViewSet(_OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = NutritionNote.objects.all()
    serializer_class = NutritionNoteSerializer
    timestamp_field = "logged_at"
    http_method_names = ["get", "post", "delete"]


@api_view(["GET"])
def health_summary(request):
    window = int(request.query_params.get("window", "7"))
    if window not in (7, 30):
        window = 7
    return Response(summarize(request.user.id, window))
```

```python
# apps/health_logs/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    WeightLogViewSet, SleepLogViewSet, ActivityLogViewSet, NutritionNoteViewSet,
    health_summary,
)

router = DefaultRouter()
router.register("weight", WeightLogViewSet, basename="weight")
router.register("sleep", SleepLogViewSet, basename="sleep")
router.register("activity", ActivityLogViewSet, basename="activity")
router.register("nutrition", NutritionNoteViewSet, basename="nutrition")

urlpatterns = [
    path("summary", health_summary),
    path("", include(router.urls)),
]
```

---

## Service de Agregação

> **Crítico:** consumido pelo `ai_engine.skills.health_summary`. Mantenha contrato estável.

```python
# apps/health_logs/services/aggregate.py
from datetime import timedelta
from django.db.models import Avg, Sum
from django.utils import timezone
from ..models import WeightLog, SleepLog, ActivityLog, NutritionNote

def summarize(user_id: int, window_days: int = 7) -> dict:
    since = timezone.now() - timedelta(days=window_days)

    sleep_qs = SleepLog.objects.filter(user_id=user_id, started_at__gte=since)
    avg_sleep = sleep_qs.aggregate(a=Avg("duration_hours"))["a"]
    avg_quality = sleep_qs.aggregate(a=Avg("quality_score"))["a"]

    latest_weight = WeightLog.objects.filter(user_id=user_id).order_by("-measured_at").values_list("value_kg", flat=True).first()
    first_weight = WeightLog.objects.filter(user_id=user_id, measured_at__gte=since).order_by("measured_at").values_list("value_kg", flat=True).first()
    weight_trend = float(latest_weight - first_weight) if (latest_weight and first_weight) else None

    total_activity = ActivityLog.objects.filter(user_id=user_id, performed_at__gte=since).aggregate(s=Sum("duration_min"))["s"] or 0

    last_notes = list(NutritionNote.objects.filter(user_id=user_id).order_by("-logged_at").values_list("note", flat=True)[:3])

    return {
        "window_days": window_days,
        "avg_sleep_hours": float(avg_sleep) if avg_sleep is not None else None,
        "avg_sleep_quality": float(avg_quality) if avg_quality is not None else None,
        "latest_weight_kg": float(latest_weight) if latest_weight is not None else None,
        "weight_trend_kg": weight_trend,
        "total_activity_min": int(total_activity),
        "last_nutrition_notes": last_notes,
    }
```

---

## Critérios de Aceite (resumo do PRD)

- [ ] CRUD funcional com paginação default e ordenação por timestamp desc
- [ ] Filtros `from`/`to` funcionando
- [ ] Outro usuário não enxerga registros
- [ ] `health_summary` retorna `null` para campos sem dados (não erro)
- [ ] Cobertura ≥ 90% no service `aggregate`

---

## Testes obrigatórios

```python
# tests/health_logs/test_summary.py
def test_summary_with_no_logs_returns_nulls(auth_client, user): ...
def test_summary_aggregates_within_window(auth_client, user, freezer): ...
def test_summary_excludes_other_users(auth_client, user, other_user): ...
def test_weight_log_validates_range(auth_client): ...
def test_user_cannot_delete_another_users_log(auth_client, other_user): ...
```

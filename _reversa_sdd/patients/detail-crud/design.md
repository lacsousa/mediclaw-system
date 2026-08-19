# Patients / Detail & CRUD, Design Técnico

> Contrato operacional de **COMO** o detalhe/edição/exclusão é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/patients/<id>/` | — | `PatientDetail` | 200, 404, 401 | `IsAuthenticated` |
| PATCH | `/api/v1/patients/<id>/` | `{subset de campos}` | `PatientListSerializer` | 200, 400, 404, 401 | `IsAuthenticated` |
| DELETE | `/api/v1/patients/<id>/` | — | `204 No Content` | 204, 404, 401 | `IsAuthenticated` |

## Fluxo Principal

1. `Patient.objects.filter(doctor=request.user).get(pk=id)` — se `DoesNotExist` → `AppError("NOT_FOUND", ..., 404)`. (`apps/patients/views.py:58-59,62`) 🟢
2. **GET:** serializa com `PatientDetailSerializer` — inclui `weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes` e `conversations` (não-deletadas, ordenadas por `-updated_at`). (`views.py:64-70`) 🟢
3. **PATCH:** `PatientListSerializer(patient, data=request.data, partial=True)`; valida e `save()`. (`views.py:74-79`) 🟢
4. **DELETE:** `patient.delete()` → `204`. (`views.py:84-85`) 🟢

## Fluxos Alternativos

- **[Fora do escopo / inexistente]:** mesmo `404 NOT_FOUND` (anti-reconhecimento de existência). (`views.py:59-62`) 🟢
- **[PATCH inválido]:** 400 `VALIDATION_ERROR`. (`views.py:77-78`) 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.health_logs.models` | Histórico no detalhe | `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` |
| `apps.conversations.models.Conversation` | Conversas do paciente | `related_name="conversations"`, filtro `deleted_at__isnull=True` |
| `apps.common.exceptions.AppError` | 404 uniforme | `NOT_FOUND` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| 404 para fora do escopo em vez de 403 (não vaza existência) | `views.py:58-62` | 🟢 |
| `SET_NULL` na FK `Conversation.patient` (delete não apaga conversas) | `conversations/models.py:15` | 🟢 |
| Serializer único para list e PATCH; detalhe com sub-serializers | `serializers.py` | 🟢 |

## Riscos e Lacunas

- 🟡 Detalhe carrega todos os logs + conversas em uma resposta — avaliar paginação/lazy loading para pacientes com muitos registros.

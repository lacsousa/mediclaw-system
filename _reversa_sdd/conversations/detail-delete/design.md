# Conversations / Detail & Delete, Design Técnico

> Contrato operacional de **COMO** o detalhe/exclusão é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/conversations/<id>/` | — | `Conversation + messages` | 200, 404, 401 | `IsAuthenticated` |
| DELETE | `/api/v1/conversations/<id>/` | — | 204 | 204, 404, 401 | `IsAuthenticated` |

## Fluxo Principal

1. `conv = Conversation.objects.get(pk=id, doctor=request.user)`; `DoesNotExist` → `AppError("NOT_FOUND", ..., 404)`. (`apps/conversations/views.py`) 🟢
2. **GET:** `messages = conv.messages.all()`; serializa conversa + mensagens → `200`. (`views.py`) 🟢
3. **DELETE:** `conv.deleted_at = timezone.now()`; `conv.save(update_fields=["deleted_at"])` → `204`. (`views.py`) 🟢

## Fluxos Alternativos

- **[Fora do escopo/inexistente]:** 404 uniforme. (`views.py`) 🟢
- **[Soft-deletada consultada pelo id]:** como `objects` exclui `deleted_at`, `get` falha → 404. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.conversations.models.Message` | Mensagens no detalhe | `conv.messages.all()` |
| `apps.common.exceptions.AppError` | 404 uniforme | `NOT_FOUND` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Soft delete em vez de `delete()` físico | `views.py`; `models.py` | 🟢 |
| Dois managers (`objects` e `all_objects`) | `models.py` | 🟢 |
| 404 para fora do escopo (anti-reconhecimento) | `views.py` | 🟢 |

## Riscos e Lacunas

- 🟡 Soft delete mantém dados de saúde (mensagens) no banco — avaliar política de retenção/expurgo (90 dias LGPD).

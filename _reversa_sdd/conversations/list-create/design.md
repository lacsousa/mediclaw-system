# Conversations / List & Create, Design Técnico

> Contrato operacional de **COMO** listar/criar conversas é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/conversations/` | `?page=` | `{results, count, next}` | 200, 401 | `IsAuthenticated` |
| POST | `/api/v1/conversations/` | — | `Conversation` | 201, 401 | `IsAuthenticated` |

## Fluxo Principal

1. **GET:** `qs = Conversation.objects.filter(doctor=request.user).select_related("patient")` (manager exclui soft-deletadas). (`apps/conversations/views.py`) 🟢
2. `total = qs.count()`; `offset = (page-1)*20`; `items = qs[offset:offset+20]`. (`views.py`) 🟢
3. `next = "?page=N+1"` se `offset+20 < total`, senão `null`. (`views.py`) 🟢
4. **POST:** `Conversation.objects.create(doctor=request.user, title="Nova conversa")` → `201`. (`views.py`) 🟢
5. Renderer global envolve em `{data, error: null, meta: {}}`. 🟢

## Fluxos Alternativos

- **[Página além do fim]:** `next=null`, itens vazios. 🟡
- **[Sem conversas]:** `results: []`, `count: 0`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.conversations.models.Conversation` | Dados | manager + `select_related` |
| `apps.common.renderers.EnvelopeJSONRenderer` | Envelope | via settings |
| `apps.common.permissions.IsAuthenticated` (default) | Proteção | `permission_classes` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Soft delete via manager (exclui `deleted_at IS NOT NULL`) | `models.py` | 🟢 |
| Paginação manual consistente com patients | `views.py` | 🟢 |
| `select_related("patient")` evita N+1 | `views.py` | 🟢 |

## Riscos e Lacunas

- 🟡 Listagem manual não expõe `patient` aninhado completo — validar shape esperado pelo frontend.

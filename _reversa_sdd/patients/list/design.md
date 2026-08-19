# Patients / List, Design Técnico

> Contrato operacional de **COMO** a listagem é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/patients/` | `?page=` | `{results, count, next}` | 200, 401 | `IsAuthenticated` |

## Fluxo Principal

1. `qs = Patient.objects.filter(doctor=request.user)` — escopo do dono. (`apps/patients/views.py:41`) 🟢
2. `_annotate_patients(qs)`:
   - `conversation_count`: `Count` de conversas `deleted_at__isnull=True`. (`views.py:18-20`) 🟢
   - `last_seen_at`: `Max(updated_at)` de conversas não-deletadas. (`views.py:21-22`) 🟢
   - `latest_weight_kg`: subquery top-1 por `measured_at`. (`views.py:23-28`) 🟢
3. `total = qs.count()`; `items = qs[offset:offset+20]` (paginação manual com slicing). (`views.py:30-33`) 🟢
4. `next = page+1` se `offset+20 < total`, senão `null`. (`views.py:34-37`) 🟢
5. Serializa com `PatientListSerializer(many=True)` → `200 {results, count, next}`. 🟢

## Fluxos Alternativos

- **[Página além do fim]:** `next=null`; itens vazios. 🟡
- **[Sem pacientes]:** `results: []`, `count: 0`, `next: null`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.health_logs.models.WeightLog` | Anotação de peso | Subquery `latest_weight_kg` |
| `apps.conversations.models.Conversation` | Anotações de atividade | `Count`/`Max` por `doctor` |
| `apps.common.permissions.IsAuthenticated` (default) | Proteção da rota | `permission_classes` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Paginação manual (`offset/limit` + `next`) em vez do `DefaultPagination` global | `views.py:30-37` | 🟢 |
| Anotação por subquery para evitar N+1 | `views.py:23-28` | 🟢 |

## Riscos e Lacunas

- 🟡 Inconsistência de padrão: paginação manual aqui vs `DefaultPagination` global (renderer usa envelope, mas este endpoint retorna `{results, count, next}` direto).
- 🟢 Sem testes dedicados para `patients` no legado — cobertura via fluxos de chat/health_logs.

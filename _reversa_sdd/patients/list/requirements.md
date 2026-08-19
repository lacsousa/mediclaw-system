# Patients / List — Requisitos

> Contrato operacional do caso de uso **Listar pacientes** (`GET /api/v1/patients/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Lista os pacientes do médico autenticado com paginação manual (20/página) e anotações derivadas: `conversation_count`, `last_seen_at` e `latest_weight_kg`. O escopo é sempre `doctor=request.user`.

## Regras de Negócio

- **RN-01** — Listagem filtrada por `doctor=request.user`. 🟢
- **RN-02** — `conversation_count` e `last_seen_at` consideram apenas conversas **não** soft-deletadas (`deleted_at__isnull=True`). 🟢
- **RN-03** — `latest_weight_kg` = top-1 peso por `measured_at` via subquery. 🟢
- **RN-04** — Paginação manual: `offset/limit` (20), `next` com `?page=N+1` quando houver mais. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Listar pacientes com anotações | Must | GET `/api/v1/patients/` → 200 `{results, count, next}`; itens com `conversation_count`, `last_seen_at`, `latest_weight_kg` |
| RF-02 | Paginar com `next` correto | Must | 45 pacientes → página 3 com 5 itens, `count=45`, `next=null` |

## Critérios de Aceitação

```gherkin
Dado um médico autenticado com 3 pacientes (1 sem conversas)
Quando faço GET em /api/v1/patients/
Então recebo 200 com 3 itens, cada um com conversation_count, last_seen_at e latest_weight_kg

Dado um médico com 45 pacientes
Quando faço GET em /api/v1/patients/?page=3
Então recebo 5 itens, count=45 e next=null
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/patients/views.py:13-46` | `_annotate_patients`, `list_patients` | 🟢 |
| `apps/patients/models.py` | `Patient`, índices | 🟢 |
| `apps/health_logs/models.py` | `WeightLog` (anotação `latest_weight_kg`) | 🟢 |

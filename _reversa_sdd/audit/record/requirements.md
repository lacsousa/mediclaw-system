# Audit / Record — Requisitos

> Contrato operacional do caso de uso **Registro de evento de auditoria** (`record`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Contrato da camada de auditoria: `record(event, *, user=None, **kwargs)` deve persistir eventos operacionais e de conformidade. **No MVP é um stub `pass`** — a assinatura documenta o contrato, mas nada é registrado (ADR 007 "auditoria adiada"). A unit `audit` não possui endpoints próprios; seu urlconf roteia views de outras units sob `/api/v1/admin/`.

## Regras de Negócio

- **RN-01** — `record(event: str, *, user=None, **kwargs) -> None`. 🟢
- **RN-02** — Corpo é `pass` — nenhum efeito no MVP. 🟢
- **RN-03** — Nenhum modelo `ActivityLog` implementado (ausência de `models.py`/migrations). 🟢
- **RN-04** — App `audit` funciona como **roteador admin**: monta `admin_create_user` (accounts) e `metrics` (rag) sob `/api/v1/admin/`. 🟢
- **RN-05** — Eventos documentados hoje: `GUARDRAIL_BLOCKED`, `MESSAGE_SENT` (ai_engine), `KB_UPLOAD`, `KB_DELETE` (rag), `ADMIN_CREATED_USER` (accounts). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Persistir evento de auditoria | Must (pós-MVP) | `record("GUARDRAIL_BLOCKED", metadata={reason})` grava um registro auditável |
| RF-02 | Registrar chamadores sem quebrar | Must (hoje) | Chamadas de `record` dos apps não lançam erro (stub seguro) |
| RF-03 | Roteamento admin funcional | Must | `/api/v1/admin/users/` e `/api/v1/admin/metrics/` respondem (views delegadas) |

## Critérios de Aceitação

```gherkin
Dado o MVP com record como stub
Quando um app chama record("MESSAGE_SENT", metadata={...})
Então a chamada não lança erro e nada é persistido

Dado um usuário ADMIN
Quando consulto /api/v1/admin/metrics/
Então recebo as métricas agregadas (view delegada da unit rag)

Dado o caminho /api/v1/admin/knowledge/metrics/
Quando consulto
Então recebo 404 (a rota metrics vive no urlconf audit, não no rag)
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/audit/services/log.py:1-4` | `record` — stub `pass` | 🟢 |
| `apps/audit/urls.py:6-9` | roteamento `users/` e `metrics/` | 🟢 |
| `apps/ai_engine/orchestrator.py:200,226,245` | chamadas `GUARDRAIL_BLOCKED`/`MESSAGE_SENT` | 🟢 |
| `apps/rag/views.py:46-50,130-131` | chamadas `KB_UPLOAD`/`KB_DELETE` | 🟢 |
| `apps/accounts/views.py:63` | chamada `ADMIN_CREATED_USER` | 🟢 |

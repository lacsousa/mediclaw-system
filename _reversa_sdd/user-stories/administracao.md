# User Stories — Administração e Auditoria

> Fluxo: métricas operacionais, roteamento admin e trilha de auditoria.
> Cobertura: módulo `audit` (+ view `metrics` da unit `rag`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-ADM-01 — Ver métricas operacionais do dia

**Como** administrador,
**quero** ver métricas agregadas (usuários, conversas, mensagens, tokens, guardrails, documentos indexados),
**para** monitorar o uso da plataforma.

- Critérios de aceite:
  - GET `/api/v1/admin/metrics/` → `{users_total, conversations_total, messages_today, tokens_today, guardrail_blocks_today, kb_documents_indexed}`.
  - Restrito a role `ADMIN` → 403 `FORBIDDEN`.
  - ⚠️ Rota real: `/api/v1/admin/metrics/` (registrada no urlconf do audit), **não** `/api/v1/admin/knowledge/metrics/` (404). 🟢

## US-ADM-02 — Roteamento admin central

**Como** plataforma,
**quero** concentrar as rotas de administração sob `/api/v1/admin/`,
**para** ter um ponto único de gestão.

- Critérios de aceite:
  - `/api/v1/admin/users/` (criação de usuário, de `accounts`) e `/api/v1/admin/metrics/` (de `rag`) montadas via `apps/audit/urls.py`.
  - 🟡 Acoplamento: `audit` importa views de `accounts` e `rag` — dificulta rastreabilidade.

## US-ADM-03 — Trilha de auditoria (pós-MVP)

**Como** plataforma,
**quero** registrar eventos operacionais (`GUARDRAIL_BLOCKED`, `MESSAGE_SENT`, `KB_UPLOAD`, `KB_DELETE`, `ADMIN_CREATED_USER`, `USER_REGISTERED`),
**para** cumprir LGPD e auditar o uso da IA.

- Critérios de aceite:
  - `record(event, *, user=None, **kwargs)` persistindo em `ActivityLog` (hoje é **stub `pass`** — ADR 007 "auditoria adiada").
  - Metadados sem PII (nunca conteúdo de mensagens ou dados biométricos).
  - 🔴 Lacuna: sem trilha de auditoria em produção no MVP. 🟢

## US-ADM-04 — Retenção e exclusão LGPD

**Como** plataforma,
**quero** respeitar a retenção de 90 dias e o cascade delete de dados de saúde,
**para** estar em conformidade com a LGPD.

- Critérios de aceite:
  - Ao deletar usuário, conversas, mensagens e logs de saúde são removidos (cascade via FKs). 🟢 [Revisão Codex]
  - Conversas retidas por `CONVERSATION_RETENTION_DAYS` (90) após última atividade.
  - 🔴 Lacuna: **retenção de 90 dias não implementada** (sem job de expurgo) — cascade delete **está implementado** por `on_delete=CASCADE` em pacientes/conversas/logs. 🟢/🔴 [Revisão Codex]

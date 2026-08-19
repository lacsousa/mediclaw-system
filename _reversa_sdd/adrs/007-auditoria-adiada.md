# ADR-007 — Auditoria adiada para o Epic 3 (stub `record`)

**Status:** Aceito (provisório) 🟢
**Data:** MVP atual (stub presente; expansão prevista no Epic 3)
**Fonte:** `apps/audit/services/log.py:1-4` (comentário "Será expandido no Epic 3"), `code-analysis.md` (módulo audit), `TASKS.md`.

## Contexto

O domínio exige rastreabilidade (LGPD, uso de LLM, guardrails). Implementar um pipeline completo de auditoria no MVP aumentaria escopo e complexidade (nova tabela, filas, admin). A decisão foi **adiar** a persistência e manter apenas o contrato de chamada.

## Decisão

- `record(event, *, user=None, **kwargs)` é um **stub `pass`** — eventos são descartados silenciosamente no MVP.
- Eventos já instrumentados: `USER_REGISTERED`, `LOGIN`, `ADMIN_CREATED_USER`, `GUARDRAIL_BLOCKED` (×2), `MESSAGE_SENT`, `KB_UPLOAD`, `KB_DELETE`.
- **Nunca logar conteúdo de mensagens**: apenas metadados (`conversation_id`, `tokens_used`, `latency_ms`, `reason`).
- `Message.metadata` já guarda `citations`, `onboarding_mode`, `missing_basics`, `data_capture` (fonte parcial de rastreabilidade pós-fato).

## Consequências

- **Sem trilha de auditoria real no MVP** — impossível auditar uso de IA a posteriori; mitigado por `Message.metadata` e logs estruturados (structlog).
- **Contrato divergente:** alguns chamadores usam `user=` e outros `user_id=` (cai em `**kwargs`) — a assinatura precisa ser padronizada antes do Epic 3.
- A lacuna de retenção LGPD (90 dias) permanece aberta (ver `state-machines.md`).

## Alternativas consideradas

- Implementar `ActivityLog` no MVP — postergado (Epic 3).
- Auditoria via logs estruturados apenas — já é o comportamento de facto; persistência estrutural fica para o Epic 3.

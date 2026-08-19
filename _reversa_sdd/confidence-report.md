# Relatório de Confiança — MediClaw

> Gerado pelo Revisor em 2026-08-19.
> Escala: 🟢 CONFIRMADO (extraído do código) | 🟡 INFERIDO | 🔴 LACUNA.
> Método: contagem de marcadores de confiança nos arquivos canônicos (`requirements.md` + `design.md`), globais e user stories, excluindo legendas.

---

## Resumo Geral

| Nível | Quantidade | Percentual |
|-------|-----------|------------|
| 🟢 CONFIRMADO | 1619 | 85.3% |
| 🟡 INFERIDO   | 190  | 10.0% |
| 🔴 LACUNA     | 89   | 4.7% |
| **Total**     | 1898 | 100% |

**Confiança geral:** **90.3%** — `(1619 + 190×0.5) / 1898`

---

## Revisão Cruzada

- Engine externa consultada: **Codex**
- Apontamentos recebidos: **45** (P-01 a P-45)
- Aceitos e incorporados nas specs: **23** (com origem `[Revisão Codex]`)
- Rejeitados: **0**
- Pendentes (registrados como lacunas/perguntas): **22** — ver `gaps.md` e `questions.md`

Os apontamentos aceitos corrigiram: símbolos e wire format do SSE (P-03/P-17/P-18), throttle do stream (P-19), DISCLAIMER no stream (P-22), caminho de métricas (P-24), envelope do health (P-27), validações HTTP vs chat (P-14/P-41), contrato de `/me` e OpenAPI (P-09/P-21), e reclassificações 🟢→🟡 (P-37/P-40/P-42/P-43/P-44/P-45).

---

## Por Spec

| Spec | 🟢 | 🟡 | 🔴 | Confiança |
|------|----|----|-----|-----------|
| `accounts/` | 155 | 16 | 9 | 91% |
| `ai_engine/` | 249 | 23 | 13 | 91% |
| `audit/` | 47 | 4 | 2 | 92% |
| `common/` | 75 | 9 | 5 | 89% |
| `conversations/` | 194 | 22 | 10 | 91% |
| `health_logs/` | 112 | 20 | 2 | 91% |
| `patients/` | 124 | 14 | 2 | 94% |
| `rag/` | 176 | 20 | 11 | 90% |
| Globais (domain, architecture, data-dictionary, erd, permissions, state-machines, code-analysis, …) | 448 | 60 | 28 | 89% |
| `user-stories/` | 39 | 2 | 7 | 83% |

---

## Lacunas Pendentes 🔴

Itens que permaneceram sem confirmação após a revisão (detalhe em `gaps.md`):

- **LGPD/compliance:** retenção 90 dias sem expurgo; auditoria stub (`record()` = `pass`).
- **Segurança:** KB sem escopo ao uploader; services de paciente sem validação de tenant; dedup não transacional.
- **Integridade:** atomicidade Postgres ↔ ChromaDB ausente.
- **Contratos de API:** `ValidationError` → `UNHANDLED`; código de limite canônico indefinido.
- **Streaming:** DISCLAIMER ausente; guardrail de saída pós-hoc; turno órfão; sem throttle.
- **Entrada:** query params inválidos → 500; `persist_user_name` inexistente → 500.
- **Provedores/métricas:** Anthropic documentado ausente; `tokens_used` conta palavras; catch-alls mascarando erros.
- **OpenAPI/user-stories:** contrato OpenAPI não confiável para geração de clientes (P-01/P-08/P-10 a P-13/P-15/P-16).

Perguntas correspondentes: [`questions.md`](questions.md) (20 perguntas aguardando validação).

---

## Recomendações

- [ ] **Prioridade 1 — contratos:** definir código canônico do limite (Q3) e normalizar `ValidationError` → `VALIDATION_ERROR` (Q4); sem isso, frontend/OpenAPI consomem erros errados.
- [ ] **Prioridade 1 — LGPD:** decidir se retenção 90 dias e auditoria entram no MVP (Q1/Q2) — são os dois maiores riscos de conformidade.
- [ ] **Prioridade 2 — streaming:** decidir mecanismo do DISCLAIMER (Q6), aceitar guardrail pós-hoc (Q7) e estado de turno (Q8); caminho de maior uso do frontend.
- [ ] **Prioridade 2 — segurança:** definir modelo de permissão da KB (Q10) e validação de tenant nos services (Q13).
- [ ] **Prioridade 3 — robustez:** tratar query params inválidos (Q16) e `persist_user_name` (Q15); regerar OpenAPI após as decisões (P-01/P-08/P-10..P-16).
- [ ] **Manutenção:** remover código morto (`GuardrailBlockedError`, `IsOwner`) ou documentar intenção (Q17); centralizar env do RAG em `settings.py` (Q18).

---

## Histórico de Reclassificações

Reclassificações aplicadas nesta revisão (com origem `[Revisão Codex]`):

| De | Para | Afirmação | Evidência |
|----|------|-----------|-----------|
| 🟢 | 🟡 | "Captura nunca quebra o turno" — persist de health data captura só `ValidationError` | `user_data_capture.py:156-207` |
| 🟢 | 🟡 | `user_id` bindado em logs JWT | `common/middleware.py` vs ordem de auth DRF |
| 🟢 | 🟡 | `complete_json` integra o Protocol de provider | `providers/base.py:9-14` |
| 🟢 | 🟡 | "Backend valida MIME" sem sniffing | `rag/views.py:30-35` (`f.content_type`) |
| 🟢 | 🟡 | Conversão L² → score como cosseno | `retriever.py:22-23,40` (vetores normalizados não fixados) |
| 🟢 | 🟡 | Ordenação por score desc no retrieval | `retriever.py` (sem `sort`) |
| 🟢 | 🟡/🔴 | Timestamp futuro em todos os logs via HTTP | `health_logs/serializers.py` (só peso) |
| 🟢 | 🟡 | Faixas de sono (`0<h≤24`) e nota mínima (10) via HTTP | `health_logs/serializers.py` (só chat) |
| — | 🟢 | `stream` **sem** throttle (RN-13 corrigido) | `conversations/views.py:105` vs `:120` |
| — | 🟢 | Métricas em `/api/v1/admin/metrics/` | `apps/audit/urls.py:8` |
| — | 🟢 | GET /me sempre 200; PATCH/DELETE existem | `accounts/views.py:66-93` |
| — | 🟢 | POST `/conversations/` ignora body (`title` fixo) | `conversations/views.py:60-62` |
| — | 🔴 | `ValidationError` DRF → `UNHANDLED` | `common/exceptions.py:36-43` |

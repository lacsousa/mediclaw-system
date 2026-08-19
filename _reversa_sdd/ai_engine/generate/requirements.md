# AI Engine / Generate — Requisitos

> Contrato operacional do caso de uso **Geração de resposta** (REST `generate` e SSE `generate_stream`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Pipeline de geração da resposta do assistente. Sem endpoints próprios (URLs vazios) — é chamado por `conversations` em `POST /messages/` (REST) e `GET /stream/` (SSE). Compõe: guardrail de entrada → captura automática → seleção de prompt por prontidão → provider → guardrail de saída → anexo de `DISCLAIMER`.

## Regras de Negócio

- **RN-01** — Entrada sempre `(user_id, conversation_id, query, is_first_message)`. 🟢
- **RN-02** — Guardrail de entrada bloqueado → resposta canônica + `DISCLAIMER`, `tokens=0`, `blocked=True`. 🟢
- **RN-03** — Guardrail de saída bloqueado → canned reply + `DISCLAIMER`, `blocked=True`. 🟢
- **RN-04** — REST: anexa `DISCLAIMER` ao final se `content` não termina com ele. 🟢
- **RN-05** — `MAX_TOKENS` lido de env `MAX_TOKENS_PER_RESPONSE` (default 800). 🟢
- **RN-06** — Nunca loga conteúdo da mensagem nem PII; apenas metadados (`guardrail_blocked`, `MESSAGE_SENT`). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Gerar resposta REST | Must | `generate(...)` → `GenerateResult {content, tokens_used, blocked_by_guardrail, citations, onboarding_mode, missing_basics, data_capture}` |
| RF-02 | Gerar resposta SSE | Must | `generate_stream(...)` → iterator de eventos `citation` → `token*` → `done` |
| RF-03 | Bloquear na entrada | Must | `check_input` bloqueado → canned reply + DISCLAIMER, `tokens=0`, `blocked=True` (e `record("GUARDRAIL_BLOCKED")`) |
| RF-04 | Bloquear na saída | Must | `check_output` bloqueado → canned reply + DISCLAIMER, `blocked=True` |
| RF-05 | Anexar disclaimer no REST | Must | `content` sem `DISCLAIMER` → concatena `\n\nDISCLAIMER` |
| RF-06 | Reportar erro no SSE | Must | Exceção no stream → evento `error` com `code: LLM_PROVIDER_ERROR` |

## Critérios de Aceitação

```gherkin
Dado um query liberado pelo guardrail de entrada
Quando chamo generate
Então retorna GenerateResult com content (DISCLAIMER anexado se ausente), tokens_used e blocked=False

Dado um query bloqueado pelo guardrail de entrada
Quando chamo generate
Então retorna GenerateResult com canned_reply + DISCLAIMER, tokens_used=0 e blocked=True

Dado um query liberado mas com saída bloqueada por check_output
Quando chamo generate
Então retorna canned_reply + DISCLAIMER e blocked=True

Dado um provider.stream que lança exceção
Quando itero generate_stream
Então recebo um evento error com code LLM_PROVIDER_ERROR
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/ai_engine/orchestrator.py:183-258` | `generate` | 🟢 |
| `apps/ai_engine/orchestrator.py:261-348` | `generate_stream` | 🟢 |
| `apps/ai_engine/orchestrator.py:31-39` | `GenerateResult` | 🟢 |
| `apps/ai_engine/guardrails.py:135-150` | `check_input`, `check_output` | 🟢 |
| `apps/ai_engine/prompts.py` | `DISCLAIMER` | 🟢 |

# AI Engine / Guardrail — Requisitos

> Contrato operacional do caso de uso **Guardrail clínico** (`check_input` / `check_output`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Camada de segurança que bloqueia solicitações de **urgência, diagnóstico e prescrição** (e entrada sem sentido) antes da geração, e padrões proibidos na saída. Não emite LLM: retorna `GuardrailResult {allowed, reason, canned_reply}` com resposta canônica.

## Regras de Negócio

- **RN-01** — Ordem fixa de checagem de entrada: **urgency → diagnosis → prescription → gibberish**. 🟢
- **RN-02** — Primeiro padrão que casar define o `reason` e o `canned_reply`; blocagem imediata. 🟢
- **RN-03** — Sem match → `allowed=True` (nenhum reason/reply). 🟢
- **RN-04** — `check_output` usa `FORBIDDEN_OUTPUT_PATTERNS` independentes da entrada. 🟢
- **RN-05** — Bloqueio dispara `record("GUARDRAIL_BLOCKED")` no orquestrador (ver generate). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Bloquear urgência | Must | Texto casando `URGENCY_PATTERNS` → `reason=urgency`, `URGENCY_REPLY` |
| RF-02 | Bloquear pedido de diagnóstico | Must | Texto casando `DIAGNOSIS_PATTERNS` → `reason=diagnosis`, `DIAGNOSIS_REPLY` |
| RF-03 | Bloquear pedido de prescrição | Must | Texto casando `PRESCRIPTION_PATTERNS` → `reason=prescription`, `PRESCRIPTION_REPLY` |
| RF-04 | Bloquear sem sentido | Must | `_is_gibberish(text)` → `reason=gibberish`, `GIBBERISH_REPLY` |
| RF-05 | Liberar texto seguro | Must | Nenhum padrão → `allowed=True` |
| RF-06 | Bloquear saída proibida | Must | `check_output` com match → `allowed=False` + reason |

## Critérios de Aceitação

```gherkin
Dado "me diga se tenho diabetes"
Quando chamo check_input
Então retorna allowed=False com reason=diagnosis e DIAGNOSIS_REPLY

Dado "quero uma receita de remédio"
Quando chamo check_input
Então retorna allowed=False com reason=prescription e PRESCRIPTION_REPLY

Dado "sinto uma dor no peito agora"
Quando chamo check_input
Então retorna allowed=False com reason=urgency e URGENCY_REPLY

Dado uma mensagem sem padrões de risco
Quando chamo check_input
Então retorna allowed=True
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/ai_engine/guardrails.py:6-11` | `GuardrailResult` | 🟢 |
| `apps/ai_engine/guardrails.py:135-144` | `check_input` (ordem fixa) | 🟢 |
| `apps/ai_engine/guardrails.py:147-150` | `check_output` | 🟢 |
| `apps/ai_engine/guardrails.py:104-132` | `_is_gibberish` | 🟢 |
| `apps/ai_engine/guardrails.py` | `URGENCY_PATTERNS`, `DIAGNOSIS_PATTERNS`, `PRESCRIPTION_PATTERNS`, `FORBIDDEN_OUTPUT_PATTERNS` | 🟢 |
| `apps/ai_engine/prompts.py` | `URGENCY_REPLY`, `DIAGNOSIS_REPLY`, `PRESCRIPTION_REPLY`, `GIBBERISH_REPLY` | 🟢 |

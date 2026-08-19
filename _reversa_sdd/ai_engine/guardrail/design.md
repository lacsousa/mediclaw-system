# AI Engine / Guardrail, Design Técnico

> Contrato operacional de **COMO** o guardrail é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `check_input` | `(text: str) -> GuardrailResult` | `{allowed, reason, canned_reply}` (`guardrails.py:135-144`) |
| `check_output` | `(text: str) -> GuardrailResult` | `{allowed, reason, canned_reply}` (`guardrails.py:147-150`) |
| `_is_gibberish` | `(text: str) -> bool` | bool (`guardrails.py:104-132`) |
| `GuardrailResult` | dataclass | `allowed: bool, reason: str = "", canned_reply: str = ""` (`guardrails.py:6-11`) |

## Fluxo Principal

1. `check_input(text)` avalia padrões em ordem fixa. (`guardrails.py:135-144`) 🟢
2. **Urgência:** `URGENCY_PATTERNS` casa → `reason="urgency"`, `canned_reply=URGENCY_REPLY`, `allowed=False`. 🟢
3. **Diagnóstico:** senão, `DIAGNOSIS_PATTERNS` casa → `reason="diagnosis"`, `DIAGNOSIS_REPLY`. 🟢
4. **Prescrição:** senão, `PRESCRIPTION_PATTERNS` casa → `reason="prescription"`, `PRESCRIPTION_REPLY`. 🟢
5. **Sem sentido:** senão, `_is_gibberish(text)` → `reason="gibberish"`, `GIBBERISH_REPLY`. 🟢
6. Nenhum match → `GuardrailResult(allowed=True)`. 🟢
7. `check_output(text)` avalia `FORBIDDEN_OUTPUT_PATTERNS`; match → `allowed=False`. 🟢

## Fluxos Alternativos

- **[Múltiplos padrões casando]:** a **primeira** checagem na ordem (urgency) vence — não há combinação de reasons. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.ai_engine.prompts.py` | Respostas canônicas | `URGENCY_REPLY`, `DIAGNOSIS_REPLY`, `PRESCRIPTION_REPLY`, `GIBBERISH_REPLY` |
| `apps.audit.services.log.record` | Auditoria (stub) | `record("GUARDRAIL_BLOCKED", metadata={reason})` no orquestrador |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Ordem fixa urgency → diagnosis → prescription → gibberish | `guardrails.py:135-144` | 🟢 |
| Padrões regex como constantes de módulo | `guardrails.py` | 🟢 |
| Guardrails sem chamada a LLM (regex/heurística pura) | `guardrails.py` | 🟢 |
| `check_output` com padrões próprios, independente da entrada | `guardrails.py:147-150` | 🟢 |

## Riscos e Lacunas

- 🟡 `FORBIDDEN_OUTPUT_PATTERNS` podem gerar falsos positivos na saída legítima — revisar expressões.
- 🟡 `_is_gibberish` é heurística de plausibilidade de palavras — avaliar limite de falsos negativos em pt-BR.
- 🟢 Auditoria do bloqueio é stub (nada persiste — ADR 007).

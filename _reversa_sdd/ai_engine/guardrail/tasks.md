# AI Engine / Guardrail, Tarefas de Implementação

> Sequência executável para reimplementar o guardrail a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Constantes de padrões (`URGENCY_PATTERNS`, `DIAGNOSIS_PATTERNS`, `PRESCRIPTION_PATTERNS`, `FORBIDDEN_OUTPUT_PATTERNS`)
- [ ] Respostas canônicas (`URGENCY_REPLY`, `DIAGNOSIS_REPLY`, `PRESCRIPTION_REPLY`, `GIBBERISH_REPLY`) em `prompts.py`

## Tarefas

- [ ] **T-01**, Dataclass `GuardrailResult {allowed, reason, canned_reply}`
  - Origem no legado: `apps/ai_engine/guardrails.py:6-11`
  - Confiança: 🟢

- [ ] **T-02**, `check_input` com ordem fixa urgency → diagnosis → prescription → gibberish
  - Origem no legado: `apps/ai_engine/guardrails.py:135-144`
  - Critério de pronto: primeiro match define reason + canned_reply; sem match → `allowed=True`
  - Confiança: 🟢

- [ ] **T-03**, `_is_gibberish` heurística de plausibilidade
  - Origem no legado: `apps/ai_engine/guardrails.py:104-132`
  - Critério de pronto: texto sem palavras plausíveis → `True`
  - Confiança: 🟢

- [ ] **T-04**, `check_output` com `FORBIDDEN_OUTPUT_PATTERNS`
  - Origem no legado: `apps/ai_engine/guardrails.py:147-150`
  - Critério de pronto: match → `allowed=False`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Urgência bloqueada com reason/canned_reply corretos
- [ ] **TT-02**, Diagnóstico bloqueado
- [ ] **TT-03**, Prescrição bloqueada
- [ ] **TT-04**, Gibberish bloqueado
- [ ] **TT-05**, Texto seguro → `allowed=True`
- [ ] **TT-06**, `check_output` bloqueia padrão proibido
- [ ] **TT-07**, Ordem: texto que casa urgência e diagnóstico → vence urgência

## Ordem Sugerida

1. T-01 → T-02 → T-03 → T-04.
2. Testes TT-01 a TT-07.

## Lacunas Pendentes (🔴)

- [ ] Revisar `FORBIDDEN_OUTPUT_PATTERNS` contra falsos positivos.
- [ ] Avaliar `_is_gibberish` em pt-BR (plausibilidade de palavras).

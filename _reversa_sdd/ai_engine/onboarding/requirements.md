# AI Engine / Onboarding — Requisitos

> Contrato operacional do caso de uso **Onboarding por prontidão** (`_resolve_messages`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Seleciona o prompt com base na **prontidão do perfil do paciente** (`get_user_readiness`). Perfil completo → modo normal (RAG + health summary). Perfil incompleto → modo **focus** (1ª mensagem, template de onboarding) ou **soft** (apêndice no prompt normal). Não é endpoint: função interna do orquestrador.

## Regras de Negócio

- **RN-01** — `readiness.is_complete` → modo normal: `_build_messages` (prompt + RAG + health summary). 🟢
- **RN-02** — Incompleto + `is_first_message` → modo `focus`: `_build_onboarding_focus_messages`, **sem citações** (`[]`). 🟢
- **RN-03** — Incompleto + não-primeira → modo `soft`: `_build_messages` com `readiness` (anexa `ONBOARDING_SOFT_APPENDIX`). 🟢
- **RN-04** — `onboarding_mode` propaga para `GenerateResult`/evento `done` (focus | soft). 🟢
- **RN-05** — `missing_basics` = `readiness.missing_*` (ou `still_missing` da captura) exposto na resposta. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Prompt normal quando perfil completo | Must | `readiness.is_complete` → `_build_messages` com RAG + health summary, `onboarding_mode` vazio |
| RF-02 | Focus na 1ª mensagem incompleta | Must | `is_first_message` + incompleto → `ONBOARDING_FOCUS_TEMPLATE`, `onboarding_mode="focus"`, sem citações |
| RF-03 | Soft em mensagens seguintes | Must | Incompleto + não-primeira → prompt normal + `ONBOARDING_SOFT_APPENDIX`, `onboarding_mode="soft"` |

## Critérios de Aceitação

```gherkin
Dado um paciente com perfil completo
Quando gero uma resposta
Então o prompt usa o modo normal com contexto RAG e health summary

Dado um paciente incompleto na primeira mensagem
Quando gero uma resposta
Então o prompt usa ONBOARDING_FOCUS_TEMPLATE e onboarding_mode=focus, sem citações

Dado um paciente incompleto em mensagens seguintes
Quando gero uma resposta
Então o prompt normal é enriquecido com ONBOARDING_SOFT_APPENDIX e onboarding_mode=soft
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/ai_engine/orchestrator.py:158-180` | `_resolve_messages` | 🟢 |
| `apps/ai_engine/orchestrator.py:115-155` | `_build_messages` | 🟢 |
| `apps/ai_engine/skills/user_readiness.py:42-78` | `get_user_readiness` | 🟢 |
| `apps/ai_engine/prompts.py` | `ONBOARDING_FOCUS_TEMPLATE`, `ONBOARDING_SOFT_APPENDIX`, `ONBOARDING_STILL_MISSING_APPENDIX` | 🟢 |

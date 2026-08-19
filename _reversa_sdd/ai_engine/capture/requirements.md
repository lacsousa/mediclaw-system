# AI Engine / Capture — Requisitos

> Contrato operacional do caso de uso **Captura automática de dados do paciente** (`capture_from_message`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Extrai dados de saúde declarados nas mensagens do chat (nome, perfil, peso, sono, atividade, nutrição), **rules-first** com LLM preenchendo lacunas, e persiste no paciente — tudo de forma automática e silenciosa. Sem endpoints próprios; chamado dentro de `generate`/`generate_stream`.

## Regras de Negócio

- **RN-01** — Mensagem sem dados de saúde (`message_likely_has_health_data` falso) → propaga `patient_id` + `still_missing`, **sem persistir**. 🟢
- **RN-02** — Extração **rules-first**: `parse_rules` (regex); LLM só quando `_should_call_llm`. 🟢
- **RN-03** — Merge `merge_extracted`: **regras vencem**, LLM preenche apenas gaps (`None`). 🟢
- **RN-04** — Sem dados acionáveis → propaga patient_id + still_missing, sem persistir. 🟢
- **RN-05** — Persistência: profile (setattr+save), weight, sleep (`quality_score or DEFAULT_SLEEP_QUALITY`), activity, nutrition; erros de validação → `result.errors`. 🟢
- **RN-06** — Paciente criado/resolvido por nome+DOB (`ensure_or_create_patient`, `resolve_patient_dob`); falhas logadas, sem quebrar o fluxo. 🟢
- **RN-07** — Nunca logar conteúdo da mensagem nem dados biométricos. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Detectar dados de saúde | Must | Texto com keywords/≥8 chars → `message_likely_has_health_data=True` |
| RF-02 | Extrair via regras | Must | `parse_rules(text)` → `ExtractedUserData` |
| RF-03 | Chamar LLM para preencher gaps | Must | `_should_call_llm` → `extract_with_llm(text)` + `merge_extracted(rules, llm)` com rules-win |
| RF-04 | Persistir dados | Must | `_persist_health_data` grava profile/weight/sleep/activity/nutrition; `result.errors` em falha |
| RF-05 | Garantir paciente | Must | `_ensure_patient` cria/resolve por nome e DOB |
| RF-06 | Retornar prontidão restante | Must | `still_missing = get_user_readiness(patient_id).to_metadata()` |

## Critérios de Aceitação

```gherkin
Dado uma mensagem "meu peso é 75 kg e durmo 7h"
Quando chamo capture_from_message
Então persiste WeightLog/SleepLog, retorna CaptureResult com saved preenchido e still_missing atualizado

Dado uma mensagem "bom dia"
Quando chamo capture_from_message
Então não persiste nada e retorna patient_id + still_missing sem alteração

Dado um peso inválido nas regras
Quando chamo capture_from_message
Então o erro aparece em result.errors sem quebrar o fluxo

Dado nome do paciente na mensagem sem paciente vinculado
Quando chamo capture_from_message
Então um Patient é criado/resolvido e vinculado à conversa
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/ai_engine/services/user_data_capture.py:26-64` | `capture_from_message` | 🟢 |
| `apps/ai_engine/services/capture_rules.py:108-172` | `parse_rules` | 🟢 |
| `apps/ai_engine/services/data_extraction_llm.py:58-72` | `extract_with_llm` | 🟢 |
| `apps/ai_engine/services/data_extraction_llm.py:75-156` | `merge_extracted` | 🟢 |
| `apps/ai_engine/services/capture_models.py:35-60` | `ExtractedUserData`, `CaptureResult` | 🟢 |
| `apps/ai_engine/skills/user_readiness.py:42-78` | `get_user_readiness` | 🟢 |

# AI Engine / Capture, Tarefas de Implementação

> Sequência executável para reimplementar a captura automática a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Models `Patient`, `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote`
- [ ] Services `ensure_or_create_patient`, `resolve_patient_dob`, `persist_*_log`
- [ ] Provider com `complete_json`

## Tarefas

- [ ] **T-01**, Dataclasses `ExtractedUserData` e `CaptureResult`
  - Origem no legado: `apps/ai_engine/services/capture_models.py:35-60`
  - Confiança: 🟢

- [ ] **T-02**, `parse_rules` rules-first (regex)
  - Origem no legado: `apps/ai_engine/services/capture_rules.py:108-172`
  - Critério de pronto: extrai name/profile/weight/sleep/activity/nutrition por regex
  - Confiança: 🟢

- [ ] **T-03**, `extract_with_llm` com `complete_json` e retorno `None` em falha
  - Origem no legado: `apps/ai_engine/services/data_extraction_llm.py:58-72`
  - Critério de pronto: `_should_call_llm` (env `DATA_CAPTURE_LLM`); pydantic/JSON/exceção → loga e retorna `None`
  - Confiança: 🟢

- [ ] **T-04**, `merge_extracted` com regras vencendo o LLM
  - Origem no legado: `apps/ai_engine/services/data_extraction_llm.py:75-156`
  - Critério de pronto: campos rules têm precedência; LLM preenche apenas ausente
  - Confiança: 🟢

- [ ] **T-05**, `capture_from_message` orquestrando detecção → extração → paciente → persistência
  - Origem no legado: `apps/ai_engine/services/user_data_capture.py:26-64`
  - Critério de pronto: sem dados → sem persistir; `_ensure_patient`; `_persist_health_data`; `still_missing` via readiness; `result.errors` em falha
  - Confiança: 🟢

- [ ] **T-06**, `_ensure_patient` com `ensure_or_create_patient`/`resolve_patient_dob` e fallback ao patient_id da conversa
  - Origem no legado: `apps/ai_engine/services/user_data_capture.py:76-127`
  - Critério de pronto: falha logada sem quebrar fluxo
  - Confiança: 🟢

- [ ] **T-07**, `_persist_health_data` para profile/weight/sleep/activity/nutrition
  - Origem no legado: `apps/ai_engine/services/user_data_capture.py:130-207`
  - Critério de pronto: grava por domain; erros de validação → `result.errors`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Mensagem com peso/sono → logs persistidos e `saved` preenchido
- [ ] **TT-02**, Mensagem sem dados → nada persistido
- [ ] **TT-03**, Peso inválido → erro em `result.errors`, fluxo não quebra
- [ ] **TT-04**, Nome do paciente → Patient criado/resolvido
- [ ] **TT-05**, LLM de extração falha → retorna `None` e regras continuam
- [ ] **TT-06**, Sem log de conteúdo/mensagem (LGPD)

## Ordem Sugerida

1. T-01 → T-02 → T-03 → T-04 → T-05 → T-06 → T-07.
2. Testes TT-01 a TT-06 (mockar LLM externo).

## Lacunas Pendentes (🔴)

- [ ] Corrigir `patient_created` (atributo `_patient_just_created` inexistente em `CaptureResult`).
- [ ] Substituir catch-all do `extract_with_llm` por tratamento específico.

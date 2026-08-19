# AI Engine / Capture, Design Técnico

> Contrato operacional de **COMO** a captura automática é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `capture_from_message` | `(conversation_id: int, doctor_id: int, text: str) -> CaptureResult` | `CaptureResult` (`services/user_data_capture.py:26-64`) |
| `parse_rules` | `(text: str) -> ExtractedUserData` | dados extraídos (`services/capture_rules.py:108-172`) |
| `extract_with_llm` | `(text: str) -> ExtractedUserData \| None` | dados via LLM ou `None` (`services/data_extraction_llm.py:58-72`) |
| `merge_extracted` | `(primary, secondary) -> ExtractedUserData` | mesclado, **rules-win** (`data_extraction_llm.py:75-156`) |
| `get_user_readiness` | `(patient_id: int \| None) -> UserReadiness` | prontidão (`skills/user_readiness.py:42-78`) |

### Dataclasses

| Tipo | Campos | Fonte |
|------|--------|-------|
| `CaptureResult` | `saved: dict`, `errors: list[dict]`, `still_missing: dict`, `patient_id`, `patient_created` | `capture_models.py:55-60` |
| `ExtractedUserData` | `name`, `profile`, `weight`, `sleep`, `activity`, `nutrition` (pydantic) | `capture_models.py:35-41` |

## Fluxo Principal

1. `message_likely_has_health_data(text)` falso (`len < 8` ou sem keywords) → propaga `patient_id` da conversa + `still_missing`, sem persistir. (`user_data_capture.py:37-41`) 🟢
2. `extracted = parse_rules(text)` — regex rules-first. (`user_data_capture.py:43`) 🟢
3. `_should_call_llm(text, extracted)` verdadeiro → `extract_with_llm(text)`; se retornou, `merge_extracted(extracted, llm_data)` (**rules vencem**). (`user_data_capture.py:44-47`) 🟢
4. Sem dados acionáveis (`has_actionable_data` falso) → propaga patient_id + still_missing, sem persistir. (`user_data_capture.py:49-53`) 🟢
5. `_ensure_patient(conversation_id, doctor_id, extracted, result)` → cria/resolve `Patient` (nome via `ensure_or_create_patient`; DOB via `resolve_patient_dob`). Falha → loga `patient_ensure_failed`/`patient_dob_resolve_failed` e volta ao patient_id da conversa. (`user_data_capture.py:55`, `user_data_capture.py:76-127`) 🟢
6. `_persist_health_data(patient_id, extracted, result)` → profile (`setattr` + `save(update_fields=...)`), weight (`persist_weight_log`), sleep (`persist_sleep_log`, `quality_score or DEFAULT_SLEEP_QUALITY`), activity (`persist_activity_log`), nutrition (`persist_nutrition_note`). Erros de validação → `result.errors`. (`user_data_capture.py:130-207`) 🟢
7. `still_missing = get_user_readiness(patient_id).to_metadata()`; retorna `result`. (`user_data_capture.py:62-64`) 🟢

### Extração LLM — `extract_with_llm` / `merge_extracted`

1. `_should_call_llm`: env `DATA_CAPTURE_LLM` (default true); falso → `False`; sem dados de saúde → `False`; senão `len(text) >= 5 or has_actionable_data`. (`data_extraction_llm.py:50-55`) 🟢
2. `get_provider().complete_json([system=EXTRACTION_SYSTEM, user=text], max_tokens=400)` → parse JSON → `ExtractedUserData.model_validate`. Falha (pydantic/JSON/qualquer exceção) → loga `llm_extraction_failed` e retorna `None`. (`data_extraction_llm.py:61-72`) 🟢
3. `merge_extracted`: campo das rules tem precedência; LLM preenche apenas ausente. (`data_extraction_llm.py:75-156`) 🟢

## Fluxos Alternativos

- **[Mensagem sem dados de saúde]:** propaga patient_id + still_missing, sem persistir nem chamar LLM. 🟢
- **[Regras sem dados acionáveis]:** mesmo caminho — retorna sem persistir. 🟢
- **[Falha ao garantir paciente por nome]:** loga `patient_ensure_failed` e volta ao patient_id da conversa. 🟢
- **[Falha ao resolver DOB]:** loga `patient_dob_resolve_failed` e continua com o paciente corrente. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.patients.models.Patient` | Vínculo e perfil | `_ensure_patient` cria/resolve; `get_user_readiness` lê perfil |
| `apps.health_logs.services.persist` | Persistência | `persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` (`user_data_capture.py:6-12,159-207`) |
| `apps.patients.services.patient` | Resolução | `ensure_or_create_patient`, `resolve_patient_dob` |
| `apps.ai_engine.providers.get_provider` | LLM | `complete_json` no `extract_with_llm` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Captura rules-first; LLM só preenche gaps (rules-win) | `data_extraction_llm.py:75-156`; `user_data_capture.py:43-47` | 🟢 |
| Silenciosa: falhas logadas, nunca quebram o turno — 🟡 parcial: `ensure_or_create_patient`/`resolve_patient_dob` são embrulhados em `except Exception` (🟢); a persistência de health data captura **apenas `serializers.ValidationError`** — conversões numéricas (`float()`/`int()`), `Patient.DoesNotExist` no perfil e erros de banco podem escapar do turno | `user_data_capture.py:72,96,115,156-207` | 🟡 [Revisão Codex] |
| `_should_call_llm` controlado por env `DATA_CAPTURE_LLM` (default true) | `data_extraction_llm.py:50-55` | 🟢 |
| Catch-all `except ... Exception` no `extract_with_llm` | `data_extraction_llm.py:70` | 🟢 |

## Riscos e Lacunas

- 🔴 `patient_created` derivado de `getattr(result, "_patient_just_created", False)` — atributo inexistente em `CaptureResult` (`user_data_capture.py:124`); nunca `True`.
- 🔴 Catch-all no `extract_with_llm` engole qualquer erro como `None` silencioso — sem diagnóstico de causa.
- 🟡 Env `DATA_CAPTURE_LLM` lido por chamada — padrão consistente com `RAG_TOP_K`, mas divergente de `HISTORY_WINDOW` (module scope).

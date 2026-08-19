# AI Engine / Onboarding, Design Técnico

> Contrato operacional de **COMO** o onboarding é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `_resolve_messages` | `(patient_id, conversation_id, query, is_first_message, *, capture=None) -> (messages, citations, onboarding_mode, missing_basics)` | tupla | `orchestrator.py:158-180` |
| `get_user_readiness` | `(patient_id: int \| None) -> UserReadiness` | `{is_complete, missing_name, missing_profile_fields, missing_weight_log}` | `skills/user_readiness.py:42-78` |
| `UserReadiness` | dataclass | `is_complete, missing_*` | `skills/user_readiness.py:14-20` |

## Fluxo Principal

1. `readiness = get_user_readiness(patient_id)`. (`orchestrator.py:165`) 🟢
2. **Completo:** `_build_messages(patient_id, conversation_id, query, capture=...)` → `onboarding_mode=""`. (`orchestrator.py:166-169`) 🟢
3. **Incompleto + 1ª:** `_build_onboarding_focus_messages(...)` → `onboarding_mode="focus"`, `citations=[]`. (`orchestrator.py:171-176`) 🟢
4. **Incompleto + não-primeira:** `_build_messages` com `readiness` → `onboarding_mode="soft"`. (`orchestrator.py:178-180`) 🟢

### Montagem do prompt normal — `_build_messages` (`orchestrator.py:115-155`)

1. `chunks = search(query, k=RAG_TOP_K, min_score=RAG_MIN_SCORE)` — env `RAG_TOP_K` (5), `RAG_MIN_SCORE` (0.75). (`orchestrator.py:124-128`) 🟢
2. `rag_context` = chunks formatados com `CITATION_LINE` (`- {content} (fonte: {source})`) ou fallback `"(sem evidências específicas...)"`. (`orchestrator.py:129-135`) 🟢
3. `health_summary(patient_id)` serializado `json.dumps` no system prompt. (`orchestrator.py:136-140`) 🟢
4. `SYSTEM_PROMPT_TEMPLATE.format(health_summary=..., rag_context=...)`; `_append_capture_context` anexa `DATA_CAPTURE_SAVED_APPENDIX` (se salvou) e `ONBOARDING_STILL_MISSING_APPENDIX` (se faltando). (`orchestrator.py:141`, `orchestrator.py:62-71`) 🟢
5. Incompleto → anexa `ONBOARDING_SOFT_APPENDIX` e `_onboarding_metadata(readiness, "soft")`. (`orchestrator.py:145-148`) 🟢
6. `messages = [system, *_history_with_query(conversation_id, query)]`; `citations = [{source, chunk_id}]`. (`orchestrator.py:150-155`) 🟢

## Fluxos Alternativos

- **[`patient_id=None`]:** `get_user_readiness(None)` trata ausência de perfil → incompleto. 🟡
- **[RAG sem chunks]:** contexto de fallback `"(sem evidências específicas...)"` — sem quebrar o prompt. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.rag.retriever.search` | Contexto científico | `_build_messages` recupera top-k (`orchestrator.py:124-128`) |
| `apps.ai_engine.skills.health_summary` | Resumo de saúde | `health_summary(patient_id)` delega a `health_logs.services.aggregate.summarize` |
| `apps.conversations.models.Message` | Histórico de turnos | `_history_with_query` últimos `HISTORY_WINDOW` |
| `apps.ai_engine.prompts` | Templates | `SYSTEM_PROMPT_TEMPLATE`, focus, soft, still-missing, capture-saved |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Prontidão dirige o modo de prompt (normal/focus/soft) | `orchestrator.py:158-180`; `prompts.py:33-54` | 🟢 |
| Focus só na 1ª mensagem e sem citações | `orchestrator.py:171-176` | 🟢 |
| RAG injetado como texto com `(fonte: {source})` | `orchestrator.py:129-135`; `prompts.py:56` | 🟢 |
| Soft reusa o prompt normal + apêndice | `orchestrator.py:145-148` | 🟢 |
| Turno USER final deduplicado no histórico | `orchestrator.py:89-97` | 🟢 |

## Riscos e Lacunas

- 🟡 `HISTORY_WINDOW`, `RAG_TOP_K`, `RAG_MIN_SCORE` lidos de env; `HISTORY_WINDOW` em module scope (só reflete em restart). `orchestrator.py:27-28,126-127` 🟢/🟡
- 🟡 `patient_id=None` → perfil tratado como incompleto — confirmar comportamento desejado.

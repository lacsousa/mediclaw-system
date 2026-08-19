# AI Engine, Design Técnico

> Contrato operacional de **COMO** a unit `ai_engine` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

A unit **não expõe endpoints HTTP próprios** (`urls.py` vazio). 🟢 É consumida por `conversations` (`POST /messages/` e `GET /stream/`) via chamada direta ao orquestrador. O contrato externo visível é o **evento SSE** produzido por `generate_stream` (documentado no fluxo 2).

### Funções / classes públicas

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `generate` | `(user_id: int, conversation_id: int, query: str, *, is_first_message: bool = False) -> GenerateResult` | `GenerateResult` | Caminho REST não-streaming (`orchestrator.py:183-258`) |
| `generate_stream` | `(user_id: int, conversation_id: int, query: str, *, is_first_message: bool = False) -> Iterator[dict]` | eventos SSE (`citation`/`token`/`done`/`error`) | Caminho streaming (`orchestrator.py:261-348`) |
| `check_input` | `(text: str) -> GuardrailResult` | `{allowed, reason, canned_reply}` | Ordem fixa: urgency→diagnosis→prescription→gibberish (`guardrails.py:135-144`) |
| `check_output` | `(text: str) -> GuardrailResult` | `{allowed, reason, canned_reply}` | Padrões `FORBIDDEN_OUTPUT_PATTERNS` (`guardrails.py:147-150`) |
| `_is_gibberish` | `(text: str) -> bool` | bool | Heurística de plausibilidade de palavras (`guardrails.py:104-132`) |
| `get_provider` | `() -> LLMProvider` | `OpenAIProvider`/`GeminiProvider` | Factory por env `LLM_PROVIDER`; desconhecido → `RuntimeError` (`providers/__init__.py:4-14`) |
| `capture_from_message` | `(conversation_id: int, doctor_id: int, text: str) -> CaptureResult` | `CaptureResult` | Captura + persistência automática (`services/user_data_capture.py:26-64`) |
| `parse_rules` | `(text: str) -> ExtractedUserData` | dados extraídos | Regex rules-first (`services/capture_rules.py:108-172`) |
| `extract_with_llm` | `(text: str) -> ExtractedUserData \| None` | dados via LLM ou `None` | `complete_json` com schema fixo (`services/data_extraction_llm.py:58-72`) |
| `merge_extracted` | `(primary: ExtractedUserData, secondary: ExtractedUserData) -> ExtractedUserData` | dados mesclados | **Rules win; LLM preenche gaps** (`data_extraction_llm.py:75-156`) |
| `get_user_readiness` | `(patient_id: int \| None) -> UserReadiness` | `{is_complete, missing_*}` | Completeness do perfil (`skills/user_readiness.py:42-78`) |
| `health_summary` | `(patient_id: int \| None, window: int = 7) -> dict` | resumo agregado | Delega a `health_logs.services.aggregate.summarize` (`skills/health_summary.py:4-15`) |
| `calculate_bmi` | `(weight_kg: float, height_cm: float) -> dict` | `{bmi, category}` | Valida `>0` via pydantic (`skills/bmi.py:9-25`) |
| `convert_units` | `(value: float, from_unit: str, to_unit: str) -> dict` | `{value, unit}` | Par não suportado → `ValueError` (`skills/unit_convert.py:15-19`) |
| `record` | `(event: str, *, user=None, **kwargs) -> None` | `None` | **Stub `pass`** — auditoria não implementada (`apps/audit/services/log.py:1-4`) |

### Dataclasses / modelos de contrato

| Tipo | Campos | Fonte |
|------|--------|-------|
| `GenerateResult` | `content`, `tokens_used`, `blocked_by_guardrail`, `citations: list[dict]`, `onboarding_mode`, `missing_basics`, `data_capture` | `orchestrator.py:31-39` |
| `GuardrailResult` | `allowed`, `reason=""`, `canned_reply=""` | `guardrails.py:6-11` |
| `CaptureResult` | `saved: dict`, `errors: list[dict]`, `still_missing: dict`, `patient_id`, `patient_created` | `capture_models.py:55-60` |
| `ExtractedUserData` | `name`, `profile`, `weight`, `sleep`, `activity`, `nutrition` (pydantic) | `capture_models.py:35-41` |
| `UserReadiness` | `is_complete`, `missing_name`, `missing_profile_fields`, `missing_weight_log` | `skills/user_readiness.py:14-20` |
| `ChatMessage` | `{role: system\|user\|assistant, content: str}` (TypedDict) | `providers/base.py:4-6` |
| `LLMProvider` | Protocol: `stream(messages, max_tokens)`, `complete(messages, max_tokens)` | `providers/base.py:9-14` |

### Eventos SSE emitidos por `generate_stream`

| Evento | Payload | Condição |
|--------|---------|----------|
| `token` | `{type: "token", content: str}` | Cada token do stream; ou o bloco inteiro (canned_reply + DISCLAIMER) quando o guardrail de entrada bloqueia |
| `citation` | `{type: "citation", source: str, chunk_id: str\|None}` | 1 por chunk RAG, antes dos tokens (`orchestrator.py:292-294`) |
| `done` | `{type, tokens_used, blocked, onboarding_mode, missing_basics, data_capture}` + `patient_id`, `patient_created`, `patient_first_name` se houver paciente | Fim do fluxo, bloqueado ou não |
| `error` | `{type: "error", code: "LLM_PROVIDER_ERROR", message}` | Exceção durante `provider.stream` (`orchestrator.py:301-303`) |

## Fluxo Principal

### 1. Geração REST — `generate` (`orchestrator.py:183-258`)

1. `started = time.time()`; `pre = check_input(query)`. (`orchestrator.py:190-191`) 🟢
2. **Bloqueado na entrada:** loga `guardrail_blocked` (phase=input, reason, user_id, conversation_id), `record("GUARDRAIL_BLOCKED")`, retorna `GenerateResult(pre.canned_reply + "\n\n" + DISCLAIMER, 0, True, [])`. (`orchestrator.py:192-201`) 🟢
3. `capture_result = capture_from_message(conversation_id, user_id, query)`; `capture_meta` = `to_metadata()` **somente se** `saved` ou `errors` não-vazios, senão `None`. (`orchestrator.py:203-208`) 🟢
4. `_resolve_messages(patient_id, conversation_id, query, is_first_message, capture=capture_result)` → `(messages, citations, onboarding_mode, missing_basics)`. (`orchestrator.py:210-213`) 🟢
5. `provider = get_provider()`; `content, tokens = provider.complete(messages, max_tokens=MAX_TOKENS)` — `MAX_TOKENS` lido de env `MAX_TOKENS_PER_RESPONSE` (default 800). (`orchestrator.py:214-215`, `orchestrator.py:28`) 🟢
6. **Bloqueado na saída:** `check_output(content)` falhou → loga `guardrail_blocked` (phase=output, reason=`output_<reason>`), `record("GUARDRAIL_BLOCKED")`, retorna `GenerateResult(post.canned_reply + DISCLAIMER, tokens, True, [], onboarding_mode, missing_basics or capture_result.still_missing, capture_meta)`. (`orchestrator.py:217-239`) 🟢
7. Se `content` não termina com `DISCLAIMER` (após `strip()`), anexa `\n\nDISCLAIMER`. (`orchestrator.py:241-242`) 🟢
8. `latency_ms`; `record("MESSAGE_SENT", metadata={tokens_used, blocked: False, latency_ms})`; retorna `GenerateResult(content, tokens, False, citations, onboarding_mode, missing_basics or still_missing, capture_meta)`. (`orchestrator.py:244-258`) 🟢

### 2. Geração streaming — `generate_stream` (`orchestrator.py:261-348`)

1. `check_input(query)` bloqueia → `yield token(canned_reply + DISCLAIMER)`, `yield done(tokens_used=0, blocked=True)`, `return`. (`orchestrator.py:268-279`) 🟢
2. `capture_from_message` e `capture_meta` idênticos ao REST. (`orchestrator.py:281-286`) 🟢
3. `_resolve_messages(...)` → citações. **Antes dos tokens**, `yield citation` por chunk. (`orchestrator.py:289-294`) 🟢
4. `provider.stream(messages, max_tokens=MAX_TOKENS)` — acumula `full` e `yield token` por token. (`orchestrator.py:296-300`) 🟢
5. **Exceção no stream:** `yield error(LLM_PROVIDER_ERROR, str(e))`, `return`. (`orchestrator.py:301-303`) 🟢
6. `text = "".join(full)`; `check_output(text)`. Se bloqueado → `yield token("\n\n[A resposta foi suprimida por política de segurança.]")` + `done(tokens_used=0, blocked=True, onboarding_mode, missing_basics or still_missing, data_capture)`. (`orchestrator.py:305-327`) 🟢
7. **Liberado:** `done_payload` com `tokens_used = len(text.split())` (palavras), `blocked=False`, flags de onboarding/capture. (`orchestrator.py:329-336`) 🟢
8. Se `capture_result.patient_id`: injeta `patient_id`, `patient_created` e `patient_first_name` (fetch extra de `Patient`, falha silenciosa). (`orchestrator.py:337-348`) 🟢

### 3. Seleção de prompt por prontidão — `_resolve_messages` (`orchestrator.py:158-180`)

1. `readiness = get_user_readiness(patient_id)`. (`orchestrator.py:165`) 🟢
2. `is_complete` → `_build_messages` (prompt normal + RAG + health summary). (`orchestrator.py:166-169`) 🟢
3. **Incompleto + 1ª mensagem** → `_build_onboarding_focus_messages`, `onboarding_mode="focus"`, **sem citações** (`[]`). (`orchestrator.py:171-176`) 🟢
4. **Incompleto + não-primeira** → `_build_messages` com `readiness` (que anexa `ONBOARDING_SOFT_APPENDIX`), `onboarding_mode="soft"`. (`orchestrator.py:178-180`) 🟢

### 4. Montagem do prompt — `_build_messages` (`orchestrator.py:115-155`)

1. `chunks = search(query, k=RAG_TOP_K, min_score=RAG_MIN_SCORE)` — env `RAG_TOP_K` (5), `RAG_MIN_SCORE` (0.75). (`orchestrator.py:124-128`) 🟢
2. `rag_context` = chunks formatados com `CITATION_LINE` (`- {content} (fonte: {source})`) ou `"(sem evidências específicas...)"`. (`orchestrator.py:129-135`) 🟢
3. `health_summary(patient_id)` → serializado `json.dumps` no system prompt. (`orchestrator.py:136-140`) 🟢
4. `SYSTEM_PROMPT_TEMPLATE.format(health_summary=..., rag_context=...)`; `_append_capture_context` anexa `DATA_CAPTURE_SAVED_APPENDIX` (se dados salvos) e `ONBOARDING_STILL_MISSING_APPENDIX` (se faltando). (`orchestrator.py:141`, `orchestrator.py:62-71`) 🟢
5. Incompleto → anexa `ONBOARDING_SOFT_APPENDIX` e `_onboarding_metadata(readiness, "soft")`. (`orchestrator.py:145-148`) 🟢
6. `messages = [system, *_history_with_query(conversation_id, query)]`; `citations = [{source, chunk_id}]`. (`orchestrator.py:150-155`) 🟢

### 5. Histórico — `_load_history` / `_history_with_query` (`orchestrator.py:78-97`)

1. Últimas `HISTORY_WINDOW` (6) mensagens por `conversation_id`, ordenadas por `-created_at`, revertidas para ordem cronológica. (`orchestrator.py:81-86`) 🟢
2. Se a última do histórico for `user` com `content == query` (persistida pelo caller antes do generate), **remove** para não duplicar o turno. (`orchestrator.py:94-96`) 🟢
3. Anexa `{"role": "user", "content": query}` ao final. (`orchestrator.py:97`) 🟢

### 6. Captura automática — `capture_from_message` (`services/user_data_capture.py:26-64`)

1. `message_likely_has_health_data(text)` falso (len < 8 ou sem keywords) → propaga `patient_id` da conversa e `still_missing` (readiness), **sem persistir nada**. (`user_data_capture.py:37-41`) 🟢
2. `extracted = parse_rules(text)` — regex rules-first. (`user_data_capture.py:43`) 🟢
3. `_should_call_llm(text, extracted)` verdadeiro → `extract_with_llm(text)` e, se retornou, `merge_extracted(extracted, llm_data)` (**rules vencem**). (`user_data_capture.py:44-47`) 🟢
4. Sem dados acionáveis → propaga patient_id + still_missing, sem persistir. (`user_data_capture.py:49-53`) 🟢
5. `_ensure_patient(conversation_id, doctor_id, extracted, result)` → cria/resolve `Patient` (nome via `ensure_or_create_patient`; DOB via `resolve_patient_dob`). (`user_data_capture.py:55`, `user_data_capture.py:76-127`) 🟢
6. `_persist_health_data(patient_id, extracted, result)` → profile (setattr + `save(update_fields=...)`), weight (`persist_weight_log`), sleep (`persist_sleep_log`, `quality_score or DEFAULT_SLEEP_QUALITY`), activity (`persist_activity_log`), nutrition (`persist_nutrition_note`). Erros de validação → `result.errors`. (`user_data_capture.py:130-207`) 🟢
7. `still_missing` = `get_user_readiness(patient_id).to_metadata()`; retorna `result`. (`user_data_capture.py:62-64`) 🟢

### 7. Extração LLM — `extract_with_llm` / `merge_extracted` (`data_extraction_llm.py:58-156`)

1. `_should_call_llm`: env `DATA_CAPTURE_LLM` (default true); falso → `False`; sem dados de saúde → `False`; senão `len(text)>=5 or has_actionable_data`. (`data_extraction_llm.py:50-55`) 🟢
2. `get_provider().complete_json([system=EXTRACTION_SYSTEM, user=text], max_tokens=400)` → parse JSON → `ExtractedUserData.model_validate`. Falha (pydantic/JSON/qualquer exceção) → loga `llm_extraction_failed` e retorna `None`. (`data_extraction_llm.py:61-72`) 🟢
3. `merge_extracted`: cada campo vindo das rules tem precedência; LLM preenche apenas `None`/ausente. (`data_extraction_llm.py:75-156`) 🟢

## Fluxos Alternativos

- **[Mensagem sem dados de saúde]:** captura propaga o `patient_id` da conversa e computa `still_missing`, mas não persiste nada nem aciona LLM. 🟢
- **[Regras sem dados acionáveis]:** mesmo caminho — retorna sem persistir. 🟢
- **[Falha ao garantir paciente por nome]:** loga `patient_ensure_failed` e volta ao `patient_id` da conversa. 🟢
- **[Falha ao resolver DOB]:** loga `patient_dob_resolve_failed` e continua com o paciente corrente. 🟢
- **[Patient inexistente ao buscar nome pós-stream]:** `except Exception: pass` — `patient_first_name` ausente no `done`, fluxo não quebra. 🟢
- **[Provider desconhecido (`LLM_PROVIDER=anthropic`)]:** `RuntimeError` do factory — sobe para o chamador (DRF handler / SSE `INTERNAL_ERROR` no view). 🟢
- **[Erro de conversão de unidade não suportada]:** `ValueError` (`unit_convert.py:18`). 🟢
- **[IMC com peso/altura <= 0]:** pydantic `Field(gt=0)` levanta `ValidationError`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.conversations.models.Message` | Histórico de turnos para o prompt | `_load_history` filtra por `conversation_id`, últimos `HISTORY_WINDOW` (`orchestrator.py:78-86`) |
| `apps.patients.models.Patient` | Vínculo e perfil do paciente | `_ensure_patient` cria/resolve; `get_user_readiness` lê `first_name`, perfil; fetch `patient_first_name` no `done` |
| `apps.health_logs.services.persist` | Persistência dos dados capturados | `persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` (`user_data_capture.py:6-12,159-207`) |
| `apps.health_logs.services.aggregate.summarize` | Resumo de saúde no prompt | `health_summary` delega (`skills/health_summary.py:15`) |
| `apps.health_logs.models.WeightLog` | Prontidão do perfil | `get_user_readiness` checa existência de peso (`user_readiness.py:71`) |
| `apps.rag.retriever.search` | Contexto científico | `_build_messages` recupera top-k chunks com score mínimo (`orchestrator.py:124-128`) |
| `apps.audit.services.log.record` | Auditoria | `GUARDRAIL_BLOCKED` e `MESSAGE_SENT` — **stub pass** (`orchestrator.py:200,226,245`) |
| `apps.common.exceptions.LLMProviderError` | Erros de provider | Providers envolvem exceções do SDK (`openai_provider.py:29,40`; `gemini_provider.py:53,67`) |
| `apps.patients.services.patient` | Resolução de paciente | `ensure_or_create_patient`, `resolve_patient_dob` (`user_data_capture.py:13`) |
| OpenAI SDK | Geração OpenAI | `OpenAI(api_key=OPENAI_API_KEY)`, model `CHAT_MODEL` default `gpt-4o-mini` (`openai_provider.py:13-14`) |
| Google GenAI SDK | Geração Gemini | `genai.Client(api_key=GOOGLE_API_KEY)`, model default `gemini-2.0-flash` (`gemini_provider.py:14-15`) |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Guardrails como camada independente (entrada e saída) com canned replies + `DISCLAIMER` | `guardrails.py` todo; `orchestrator.py:192-201,217-239,268-279,305-327` | 🟢 |
| Ordem fixa de guardrail de entrada: urgency → diagnosis → prescription → gibberish | `guardrails.py:135-144` | 🟢 |
| Captura automática **rules-first**, com LLM só preenchendo lacunas (`merge_extracted` rules-win) | `data_extraction_llm.py:75-156`; `user_data_capture.py:43-47` | 🟢 |
| Prompt selecionado pela prontidão do perfil: normal / `focus` (1ª msg) / `soft` (apêndice) | `orchestrator.py:158-180`; `prompts.py:33-54` | 🟢 |
| Provider via **factory** com `Protocol` (duck typing), OpenAI e Gemini com mesma interface | `providers/__init__.py:4-14`; `providers/base.py:9-14` | 🟢 |
| Gemini exige roles alternados: mensagens consecutivas do mesmo role são concatenadas no `_build` | `gemini_provider.py:17-34` | 🟢 |
| `tokens_used` medido de formas diferentes: REST usa `usage.total_tokens`, streaming conta `len(text.split())` | `openai_provider.py:38`; `gemini_provider.py:63-64`; `orchestrator.py:332` | 🟢 (imprecisão conhecida) |
| `DISCLAIMER` anexado no REST se ausente (`endswith`); no streaming não é anexado programaticamente | `orchestrator.py:241-242` vs `orchestrator.py:305-336` | 🟢 |
| Turno USER final deduplicado no histórico (caller persiste antes do generate) | `orchestrator.py:89-97` | 🟢 |
| RAG injetado no system prompt como contexto textual com citação `(fonte: {source})` | `orchestrator.py:129-135`; `prompts.py:56` | 🟢 |
| Auditoria via `record` como **stub** (adiada — ver ADR 007) | `apps/audit/services/log.py:1-4` | 🟢 |
| Limites de contexto lidos de env no module scope (`HISTORY_WINDOW`, `MAX_TOKENS`) em vez de `settings.py` | `orchestrator.py:27-28` | 🟢 |
| `patient_created` do `done` derivado de `getattr(result, "_patient_just_created", False)` — atributo inexistente em `CaptureResult` | `user_data_capture.py:124`; `capture_models.py:55-60` | 🟡 |
| `capture_meta` omitido do `GenerateResult` quando nada foi salvo nem há erros | `orchestrator.py:203-208,236,254-257` | 🟢 |

## Estado Interno

- **Sem modelos Django próprios.** A unit não cria tabelas; estado persistente vive em `Patient`, `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` (apps externos) e `Message` (histórico). 🟢
- **Estado de configuração** (module-scope, lido uma vez na importação): `HISTORY_WINDOW`, `MAX_TOKENS` (`orchestrator.py:27-28`); `RAG_TOP_K`, `RAG_MIN_SCORE` (lidos por chamada, `orchestrator.py:126-127`); `LLM_PROVIDER`, `DATA_CAPTURE_LLM` (lidos por chamada). 🟢
- **Templates de prompt** constantes em `prompts.py` (`SYSTEM_PROMPT_TEMPLATE`, `ONBOARDING_FOCUS_TEMPLATE`, `ONBOARDING_SOFT_APPENDIX`, `ONBOARDING_STILL_MISSING_APPENDIX`, `DATA_CAPTURE_SAVED_APPENDIX`, `CITATION_LINE`, `DISCLAIMER`). 🟢
- `GenerateResult`, `GuardrailResult`, `CaptureResult` etc. são dataclasses/pydantic imutáveis por turno — sem estado compartilhado entre chamadas. 🟢

## Observabilidade

- Logs estruturados via `get_logger(__name__)` — **nunca** conteúdo de mensagens ou PII: `guardrail_blocked` (phase, reason, user_id, conversation_id), `llm_extraction_failed` (error), `patient_ensure_failed` (conversation_id, error), `patient_dob_resolve_failed` (conversation_id, error). 🟢
- Auditoria `record("GUARDRAIL_BLOCKED", metadata={reason})` e `record("MESSAGE_SENT", metadata={tokens_used, blocked, latency_ms})` — **stub** no MVP, nada persiste. 🟢
- Latência medida **apenas no REST** (`latency_ms` em `generate`, `orchestrator.py:190,244`); o streaming não calcula latência. 🟡
- Sem métricas agregadas de uso por conversa/provedor; `tokens_used` fica só no payload/`GenerateResult`. 🟡

## Riscos e Lacunas

- 🔴 **`patient_created` nunca reporta `True`** no streaming — `getattr(result, "_patient_just_created", False)` lê atributo inexistente em `CaptureResult` (`user_data_capture.py:124`). Frontend não distingue paciente criado vs. existente.
- 🔴 **`tokens_used` no streaming conta palavras**, não tokens reais (`orchestrator.py:332`) — métricas de custo e auditoria ficam imprecisas.
- 🔴 **Auditoria é stub `pass`** — `GUARDRAIL_BLOCKED` e `MESSAGE_SENT` nunca são persistidos (ADR 007 "auditoria adiada"). Sem trilha de auditoria em produção.
- 🔴 **Catch-all no `extract_with_llm`**: `except (ValidationError, json.JSONDecodeError, AttributeError, Exception)` (`data_extraction_llm.py:70`) — qualquer erro vira `None` silencioso, sem diagnóstico de causa.
- 🔴 **Catch-all no streaming**: `except Exception` em `generate_stream` rotula qualquer erro como `LLM_PROVIDER_ERROR` (`orchestrator.py:301-303`) — bugs internos aparecem como falha de provider.
- 🔴 **`DISCLAIMER` não é anexado no streaming**: o texto final é emitido como veio do LLM; o `SYSTEM_PROMPT_TEMPLATE` menciona "o disclaimer indicado nas instruções do sistema" mas **não injeta o texto** do `DISCLAIMER` no system prompt — a conformidade LGPD no streaming depende do LLM. 🔴 (REST anexa; streaming não.)
- 🟡 **Provider Anthropic documentado mas ausente** — `get_provider` só conhece `openai`/`gemini`; `LLM_PROVIDER=anthropic` (documentado no PROJECT-CONTEXT) quebra com `RuntimeError`.
- 🟡 **`patient_first_name` no `done`** faz fetch extra e engole erros (`orchestrator.py:341-347`) — falha silenciosa, sem log.
- 🟡 **`record` chamado com `user_id` posicional? Não** — via keyword `user_id=user_id`, mas `record` ignora tudo (stub). Contrato de assinatura pode mudar quando implementado.
- 🟡 **Env lido em module scope** (`HISTORY_WINDOW`, `MAX_TOKENS`) não reflete mudanças em runtime sem reiniciar o processo; `RAG_TOP_K`/`RAG_MIN_SCORE` são lidos por chamada — inconsistência de padrão.

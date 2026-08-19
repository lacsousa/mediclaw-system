# AI Engine, Tarefas de Implementação

> Sequência executável para reimplementar a unit `ai_engine` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Unit `common` implementada — `get_logger` em `apps/common/logging_config.py`, `LLMProviderError` em `apps/common/exceptions.py`
- [ ] Unit `patients` implementada — model `Patient` (`first_name`, `birth_date`, `biological_sex`, `height_cm`) e `apps.patients.services.patient` (`ensure_or_create_patient`, `resolve_patient_dob`)
- [ ] Unit `health_logs` implementada — models `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote`; `services/persist.py` (`persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note`, `DEFAULT_SLEEP_QUALITY`); `services/aggregate.py` (`summarize`)
- [ ] Unit `conversations` implementada — model `Message` (roles USER/ASSISTANT/SYSTEM, `content`, `tokens_used`, `blocked_by_guardrail`, `metadata`)
- [ ] Unit `rag` implementada — `retriever.search(query, k, min_score)` retornando chunks `{content, source, chunk_id}`
- [ ] Unit `audit` com `record(event, *, user=None, **kwargs)` (stub `pass` aceito no MVP)
- [ ] Dependências Python: `openai`, `google-genai`, `pydantic`
- [ ] Variáveis de ambiente: `LLM_PROVIDER` (openai\|gemini), `OPENAI_API_KEY`/`GOOGLE_API_KEY`, `CHAT_MODEL` (default `gpt-4o-mini`/`gemini-2.0-flash`), `HISTORY_WINDOW` (6), `MAX_TOKENS_PER_RESPONSE` (800), `RAG_TOP_K` (5), `RAG_MIN_SCORE` (0.75), `DATA_CAPTURE_LLM` (true)

## Tarefas

- [ ] **T-01**, Dataclass `GenerateResult` e helpers de formatação de contexto
  - Origem no legado: `apps/ai_engine/orchestrator.py:31-71`
  - Critério de pronto: `GenerateResult` com `content`, `tokens_used`, `blocked_by_guardrail`, `citations: list[dict]` (default `[]`), `onboarding_mode: str|None`, `missing_basics: dict|None`, `data_capture: dict|None`; `_format_missing_list(readiness)` lista rótulos pt (`"(nenhum)"` se vazio); `_format_still_missing(capture)` monta string de perfil/nome/peso; `_append_capture_context(system, capture)` anexa `DATA_CAPTURE_SAVED_APPENDIX` (se `saved_summary_pt()` não-vazio) e `ONBOARDING_STILL_MISSING_APPENDIX` (se `still_missing` não-vazio); `_onboarding_metadata` → `(mode, readiness.to_metadata())`
  - Confiança: 🟢

- [ ] **T-02**, Guardrail de entrada `check_input` com padrões e canned replies
  - Origem no legado: `apps/ai_engine/guardrails.py:13-53,135-144`
  - Critério de pronto: `GuardrailResult` dataclass (`allowed`, `reason=""`, `canned_reply=""`); constantes `URGENCY_PATTERNS`, `DIAGNOSIS_PATTERNS`, `PRESCRIPTION_PATTERNS` e replies `URGENCY_REPLY`, `DIAGNOSIS_REPLY`, `PRESCRIPTION_REPLY`, `GIBBERISH_REPLY`; `check_input` testa **nesta ordem**: urgency → diagnosis → prescription → `_is_gibberish`; primeiro match vence e retorna `GuardrailResult(False, reason, reply)`; sem match → `GuardrailResult(True)`; `_matches` usa `re.search` com `re.IGNORECASE`
  - Confiança: 🟢

- [ ] **T-03**, Heurística de gibberish (`_is_gibberish` / `_word_is_plausible`)
  - Origem no legado: `apps/ai_engine/guardrails.py:84-132`
  - Critério de pronto: `_normalize_word` (NFKD→ASCII→lower); `_SHORT_OK_WORDS` (ok/oi/ola/sim/nao/m/f/kg/cm/h/min…); `_word_is_plausible`: palavra curta precisa estar em `_SHORT_OK_WORDS`, senão exige vogal e rejeita 6+ consoantes seguidas; `_is_gibberish`: vazio→True; só números/pontuação→False; número+letras→False; repetição `(.)\1{6,}`→True; ≥3 palavras com <34% plausíveis→True; len≤4 e nenhuma plausível→True
  - Confiança: 🟢

- [ ] **T-04**, Guardrail de saída `check_output`
  - Origem no legado: `apps/ai_engine/guardrails.py:71-77,147-150`
  - Critério de pronto: `FORBIDDEN_OUTPUT_PATTERNS` (`você tem {câncer|infarto|avc|diabetes tipo 2}`, `o paciente tem ...`, `diagnóstico é|confirmado|definitivo`, `tome \d+ mg|ml|gotas`, `paciente deve tomar \d+ mg|ml|gotas`); `check_output` → `GuardrailResult(False, "forbidden_output", DIAGNOSIS_REPLY)` se match, senão `GuardrailResult(True)`
  - Confiança: 🟢

- [ ] **T-05**, Templates de prompt e constantes
  - Origem no legado: `apps/ai_engine/prompts.py:1-60`
  - Critério de pronto: `SYSTEM_PROMPT_TEMPLATE` com placeholders `{health_summary}` e `{rag_context}` e diretrizes clínicas obrigatórias (nunca diagnosticar/prescrever, citar fonte, urgência, disclaimer); `DATA_CAPTURE_SAVED_APPENDIX` (`{saved_summary}`), `ONBOARDING_STILL_MISSING_APPENDIX` (`{still_missing}`), `ONBOARDING_FOCUS_TEMPLATE` (`{missing_list}`, proíbe responder perguntas clínicas), `ONBOARDING_SOFT_APPENDIX` (`{missing_list}`, responde mas lembra dados faltantes), `CITATION_LINE = "(fonte: {source})"`, `DISCLAIMER` (apoio à decisão, responsabilidade do médico)
  - Confiança: 🟢

- [ ] **T-06**, Factory de provider e contrato `LLMProvider`
  - Origem no legado: `apps/ai_engine/providers/__init__.py:4-14`; `apps/ai_engine/providers/base.py:4-14`
  - Critério de pronto: `ChatMessage` TypedDict (`role: Literal["system","user","assistant"]`, `content: str`); `LLMProvider` Protocol com `stream(messages, max_tokens) -> Iterator[str]` e `complete(messages, max_tokens) -> tuple[str, int]`; `get_provider()` lê `LLM_PROVIDER` (default `openai`), retorna `OpenAIProvider()`/`GeminiProvider()`, senão `RuntimeError(f"Unknown LLM_PROVIDER: {name}")`
  - Confiança: 🟢

- [ ] **T-07**, `OpenAIProvider` (stream / complete / complete_json)
  - Origem no legado: `apps/ai_engine/providers/openai_provider.py:11-52`
  - Critério de pronto: `OpenAI(api_key=os.environ["OPENAI_API_KEY"])`, model `CHAT_MODEL` default `gpt-4o-mini`; `stream` → `chat.completions.create(stream=True)`, yield `delta.content` se presente; `complete` → `(content or "", r.usage.total_tokens or 0)`; `complete_json` → `response_format={"type": "json_object"}`, retorna `content or "{}"`; qualquer exceção do SDK → `raise LLMProviderError(str(e))`
  - Confiança: 🟢

- [ ] **T-08**, `GeminiProvider` (build de roles / stream / complete / complete_json)
  - Origem no legado: `apps/ai_engine/providers/gemini_provider.py:12-83`
  - Critério de pronto: `genai.Client(api_key=os.environ["GOOGLE_API_KEY"])`, model default `gemini-2.0-flash`; `_build(messages)` → system concatenado + `contents` mapeando `assistant→model`, demais→`user`, **concatenando mensagens consecutivas do mesmo role** (Gemini exige roles alternados); `_config` → `GenerateContentConfig(system_instruction, max_output_tokens)`; `stream` → `generate_content_stream`, yield `chunk.text`; `complete` → `(response.text or "", usage.total_token_count or 0)`; `complete_json` → `response_mime_type="application/json"`; exceção → `LLMProviderError`
  - Confiança: 🟢

- [ ] **T-09**, Modelos de captura pydantic e `CaptureResult`
  - Origem no legado: `apps/ai_engine/services/capture_models.py:7-101`
  - Critério de pronto: `ExtractedProfile` (`birth_date: date|None`, `biological_sex: Literal["M","F","OTHER"]|None`, `height_cm: int|None`), `ExtractedWeight`, `ExtractedSleep`, `ExtractedActivity`, `ExtractedNutrition`, `ExtractedUserData` (com `profile` default factory); `_json_safe` converte date/datetime aninhados para ISO; `CaptureResult` com `saved`, `errors`, `still_missing`, `patient_id`, `patient_created=False`; métodos `to_metadata()`, `saved_summary_pt()` (frases pt por entidade salva)
  - Confiança: 🟢

- [ ] **T-10**, Extração por regras `parse_rules`
  - Origem no legado: `apps/ai_engine/services/capture_rules.py:16-172`
  - Critério de pronto: regex de peso kg (`_WEIGHT_KG_RE`), altura cm/m (`_HEIGHT_CM_RE`), data (`_DATE_RE` com anos <100 → 1900/2000), sexo (`_SEX_RE` → M/F/OTHER), horas de sono (`_SLEEP_HOURS_RE`/`_SLEEP_HOURS_ALT_RE`), qualidade de sono (`_SLEEP_QUALITY_RE`), atividade física (`_ACTIVITY_RE`/`_ACTIVITY_ALT_RE` + `_ACTIVITY_TYPE_MAP`), nutrição (`_NUTRITION_TRIGGERS`, note ≥10 chars até 1000), nome (`_NAME_RE`); retorna `ExtractedUserData` preenchido
  - Confiança: 🟢

- [ ] **T-11**, Detecção e acionabilidade de dados de saúde
  - Origem no legado: `apps/ai_engine/services/capture_rules.py:175-224`
  - Critério de pronto: `has_actionable_data(data)` → true se nome, perfil (birth_date/sexo/altura), peso, sono, atividade (duration+type) ou nutrição; `message_likely_has_health_data(text)` → false se `len(strip) < 8`, senão match de keywords (`kg`, `peso`, `dormi`, `paciente`, `anos`, `sexo`, …) em `text.lower()`
  - Confiança: 🟢

- [ ] **T-12**, Extração LLM opcional e merge rules-win
  - Origem no legado: `apps/ai_engine/services/data_extraction_llm.py:20-156`
  - Critério de pronto: `EXTRACTION_SYSTEM` (schema JSON fixo, "Não invente dados"); `_llm_enabled()` lê `DATA_CAPTURE_LLM` (default true); `_should_call_llm(text, rules_data)` → false se desabilitado/sem dados de saúde, senão `len>=5 or has_actionable_data`; `extract_with_llm(text)` → `complete_json([system, user], max_tokens=400)` → `json.loads` → `ExtractedUserData.model_validate`; qualquer exceção → loga `llm_extraction_failed` e retorna `None`; `merge_extracted(primary, secondary)` → **rules (primary) vencem**, LLM preenche só `None`
  - Confiança: 🟢

- [ ] **T-13**, Captura e persistência automática (`capture_from_message`)
  - Origem no legado: `apps/ai_engine/services/user_data_capture.py:26-207`
  - Critério de pronto: fluxo `capture_from_message(conversation_id, doctor_id, text) -> CaptureResult` — sem dados de saúde → propaga `patient_id` da conversa + `still_missing`, sem persistir; `parse_rules`; LLM opcional via `_should_call_llm` + `merge_extracted`; sem dados acionáveis → propaga; `_ensure_patient` (cria/resolve por nome `ensure_or_create_patient`, dedup por DOB `resolve_patient_dob`, falhas logadas `patient_ensure_failed`/`patient_dob_resolve_failed`); `_persist_health_data` (profile via setattr + `save(update_fields + ["updated_at"])`, weight/sleep/activity/nutrition via `persist_*`, erros → `result.errors` com entity); `still_missing` = `get_user_readiness(...).to_metadata()`
  - Confiança: 🟢

- [ ] **T-14**, Prontidão do perfil `get_user_readiness`
  - Origem no legado: `apps/ai_engine/skills/user_readiness.py:5-78`
  - Critério de pronto: `REQUIRED_PROFILE_FIELDS = ("birth_date", "biological_sex", "height_cm")` + `PROFILE_FIELD_LABELS` pt; `UserReadiness` dataclass (`is_complete`, `missing_name`, `missing_profile_fields`, `missing_weight_log`) com `missing_labels_pt()` e `to_metadata()`; `get_user_readiness(patient_id)` — `None`/inexistente → tudo faltando; senão checa `first_name`, campos de perfil e existência de `WeightLog`; `is_complete` = nada faltando
  - Confiança: 🟢

- [ ] **T-15**, Resumo de saúde `health_summary`
  - Origem no legado: `apps/ai_engine/skills/health_summary.py:4-15`
  - Critério de pronto: `health_summary(patient_id, window=7) -> dict`; `patient_id=None` → dict zerado (`window_days`, `avg_sleep_hours: None`, `avg_sleep_quality: None`, `latest_weight_kg: None`, `weight_trend_kg: None`, `total_activity_min: 0`, `last_nutrition_notes: []`); senão delega a `health_logs.services.aggregate.summarize(patient_id, window)`
  - Confiança: 🟢

- [ ] **T-16**, Skills auxiliares `calculate_bmi` e `convert_units`
  - Origem no legado: `apps/ai_engine/skills/bmi.py:4-25`; `apps/ai_engine/skills/unit_convert.py:1-19`
  - Critério de pronto: `calculate_bmi(weight_kg, height_cm) -> {bmi, category}` com `BMIInput(gt=0)` (pydantic valida; inválido → `ValidationError`), `bmi = round(kg/(m²),2)`, categorias `<18.5 abaixo_do_peso`, `<25 eutrofico`, `<30 sobrepeso`, `<35 grau_1`, `<40 grau_2`, senão grau_3; `convert_units(value, from_unit, to_unit) -> {value, unit}` com `CONVERSIONS` (kg↔lb, cm↔in, ml↔fl_oz), `round(...,4)`, par não suportado → `ValueError`
  - Confiança: 🟢

- [ ] **T-17**, Histórico e montagem de mensagens (`_load_history` → `_resolve_messages`)
  - Origem no legado: `apps/ai_engine/orchestrator.py:78-180`
  - Critério de pronto: `_load_history` → últimas `HISTORY_WINDOW` (6) mensagens por `conversation_id` em ordem cronológica; `_history_with_query` remove o USER final duplicado (mesmo `content` da query) e anexa `{"role":"user","content":query}`; `_build_onboarding_focus_messages` → system `ONBOARDING_FOCUS_TEMPLATE` + histórico, sem RAG; `_build_messages` → RAG (`search(query, RAG_TOP_K, RAG_MIN_SCORE)`), `health_summary`, system `SYSTEM_PROMPT_TEMPLATE`, apêndices de captura, `ONBOARDING_SOFT_APPENDIX` se incompleto, retorna `(messages, citations, onboarding_mode, missing_basics)`; `_resolve_messages` escolhe normal/focus/soft pela prontidão e `is_first_message`
  - Confiança: 🟢

- [ ] **T-18**, Geração REST `generate`
  - Origem no legado: `apps/ai_engine/orchestrator.py:183-258`
  - Critério de pronto: `generate(user_id, conversation_id, query, *, is_first_message=False) -> GenerateResult` — `check_input` bloqueia → loga `guardrail_blocked` (phase=input) + `record("GUARDRAIL_BLOCKED")`, retorna `GenerateResult(canned_reply + "\n\n" + DISCLAIMER, 0, True, [])`; captura automática (metadados só se saved/errors); `_resolve_messages`; `provider.complete(messages, max_tokens=MAX_TOKENS)`; `check_output` bloqueia → retorna bloqueado com `tokens`, `missing_basics or still_missing`, `data_capture`; se não termina com `DISCLAIMER` → anexa; `record("MESSAGE_SENT", {tokens_used, blocked: False, latency_ms})`; retorna `GenerateResult` completo
  - Confiança: 🟢

- [ ] **T-19**, Geração streaming `generate_stream` (SSE)
  - Origem no legado: `apps/ai_engine/orchestrator.py:261-348`
  - Critério de pronto: `generate_stream(...) -> Iterator[dict]` — entrada bloqueada → `yield token(canned_reply + DISCLAIMER)` + `yield done(tokens_used=0, blocked=True)`; `yield citation` por chunk antes dos tokens; `provider.stream` → `yield token` por token (acumula `full`); exceção → `yield error(LLM_PROVIDER_ERROR, message)` e encerra; `check_output(text)` bloqueia → `yield token(supressão)` + `done(blocked=True)`; liberado → `done(tokens_used=len(text.split()), blocked=False, onboarding_mode, missing_basics, data_capture)`; se `patient_id` → adiciona `patient_id`, `patient_created`, `patient_first_name` (fetch com try/except silencioso)
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, `check_input` bloqueia urgência/diagnóstico/prescrição na ordem correta (ex.: "falta de ar e dor no peito" → `urgency`, não `diagnosis`)
- [ ] **TT-02**, `check_input` bloqueia gibberish ("qwertyuiopasdfghjk" → `gibberish`; "ok" → permitido)
- [ ] **TT-03**, `check_output` bloqueia "tome 500mg" / "o paciente tem câncer"; libera resposta educativa
- [ ] **TT-04**, `get_provider`: `openai` → `OpenAIProvider`; `gemini` → `GeminiProvider`; `anthropic` → `RuntimeError`
- [ ] **TT-05**, `calculate_bmi(80, 175)` → `{bmi: 26.12, category: "sobrepeso"}`; `calculate_bmi(0, 175)` → `ValidationError`
- [ ] **TT-06**, `convert_units(1, "kg", "lb")` ≈ 2.2046; `convert_units(1, "kg", "cm")` → `ValueError`
- [ ] **TT-07**, `parse_rules` extrai de "Paciente João Silva, 80 kg, 1,75 m, dorme 6h, sexo masculino" → nome/weight/profile/sleep/sex corretos
- [ ] **TT-08**, `merge_extracted`: rules têm precedência; LLM preenche apenas gaps
- [ ] **TT-09**, `extract_with_llm` com `DATA_CAPTURE_LLM=false` → `_should_call_llm` retorna `False` (não chama provider)
- [ ] **TT-10**, `capture_from_message` happy path: mensagem com nome+peso+sono → `Patient` criado, `weight_log`/`sleep_log` persistidos, `saved` preenchido
- [ ] **TT-11**, `capture_from_message` sem dados de saúde → nada persistido, `patient_id` propagado da conversa, `still_missing` preenchido
- [ ] **TT-12**, `get_user_readiness`: paciente completo → `is_complete=True`; paciente sem peso → `missing_weight_log=True`
- [ ] **TT-13**, `generate` happy path (mock `provider.complete`): conteúdo termina com `DISCLAIMER`, `citations` preenchidos, `MESSAGE_SENT` registrado
- [ ] **TT-14**, `generate` com `check_input` bloqueado → `blocked_by_guardrail=True`, `tokens_used=0`, content = canned_reply + `DISCLAIMER` (sem chamar provider)
- [ ] **TT-15**, `generate` com `check_output` bloqueado (mock content "tome 500mg") → `blocked=True`, content = `DIAGNOSIS_REPLY` + `DISCLAIMER`
- [ ] **TT-16**, `generate` com 1ª mensagem + perfil incompleto → `onboarding_mode="focus"`, sem citações
- [ ] **TT-17**, `generate` perfil incompleto não-primeira → `onboarding_mode="soft"`
- [ ] **TT-18**, `generate_stream` happy path (mock `provider.stream`) → eventos `citation`, `token`*, `done` com `tokens_used` = palavras
- [ ] **TT-19**, `generate_stream` com exceção no `provider.stream` → evento `error` com `LLM_PROVIDER_ERROR`
- [ ] **TT-20**, `generate_stream` com `check_output` bloqueado → `done` com `blocked=True` e texto de supressão
- [ ] **TT-21**, `generate_stream` com `patient_id` → `done` inclui `patient_id`, `patient_created`, `patient_first_name`
- [ ] **TT-22**, `_history_with_query` remove USER final duplicado quando já persistido
- [ ] **TT-23**, `_build_messages` com RAG vazio → rag_context `"(sem evidências específicas...)"`
- [ ] **TT-24**, Nenhum log contém conteúdo de mensagem (inspecionar payloads de `guardrail_blocked`, `llm_extraction_failed`)

## Tarefas de Migração de Dados (se aplicável)

- n/a — reimplementação a partir do zero; a unit não cria tabelas próprias. 🟢

## Ordem Sugerida

1. T-01 (contratos) → T-05 (prompts) → T-02/T-03/T-04 (guardrails): camada sem dependências externas, testável isolada.
2. T-06 → T-08 (providers): dependem de `common.exceptions.LLMProviderError` e SDKs; testar com chaves mock.
3. T-09 → T-12 (captura: models → regras → LLM → merge): dependem de T-06; T-13 (persistência) depende das units `patients`/`health_logs`.
4. T-14 (readiness) e T-15 (health summary) dependem de `patients`/`health_logs`.
5. T-17 (montagem de mensagens) depende de T-05, T-15, `conversations.Message`, `rag.retriever`.
6. T-18 (generate) e T-19 (streaming) dependem de T-17 + providers + guardrails; **mockar LLM externo nos testes**.
7. Testes na ordem das dependências: TT-01–TT-06 (guardrails/skills) → TT-07–TT-12 (captura) → TT-13–TT-24 (orquestrador).
8. T-16 (skills) pode rodar em paralelo a qualquer etapa — sem dependências de units internas.

## Lacunas Pendentes (🔴)

- [ ] **`patient_created` nunca vira `True`**: `getattr(result, "_patient_just_created", False)` em `user_data_capture.py:124` — `CaptureResult` não tem esse atributo. Decidir se expor criação real do paciente no `done` do SSE (frontend depende disso para UX).
- [ ] **`tokens_used` no streaming conta palavras**, não tokens reais (`orchestrator.py:332`) — decidir se aceitar no MVP ou usar `usage` do provider no fim do stream.
- [ ] **Auditoria é stub `pass`** (`apps/audit/services/log.py`) — `GUARDRAIL_BLOCKED`/`MESSAGE_SENT` não persistem. Definir modelo `ActivityLog` e contrato antes de depender de auditoria.
- [ ] **`DISCLAIMER` não é anexado no streaming** e o `SYSTEM_PROMPT_TEMPLATE` não injeta o texto do disclaimer (só o referencia) — validar conformidade LGPD no modo SSE.
- [ ] **Catch-all no `extract_with_llm`** (`data_extraction_llm.py:70`) e **no `generate_stream`** (`orchestrator.py:301-303`) mascaram erros reais — refinar tratamento.
- [ ] **Provider Anthropic documentado mas ausente** no factory — confirmar se entra no roadmap (PROJECT-CONTEXT lista `anthropic` como opção).

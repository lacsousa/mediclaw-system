# AI Engine — Requisitos

> Contrato operacional da unit `ai_engine` (orquestração da camada de IA).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Camada de orquestração da IA do MediClaw, sem endpoints próprios (`urls.py` vazio) — exposta indiretamente via `conversations` (`/messages/` e `/stream/`). Monta o prompt do LLM (system + histórico + contexto RAG + resumo de saúde), aplica guardrails de entrada e saída (pedido de diagnóstico/prescrição/urgência/gibberish), captura automaticamente dados do paciente a partir da mensagem (regex rules-first, LLM preenche lacunas) e delega a geração ao provider configurado (OpenAI ou Gemini). Inclui skills auxiliares: IMC, conversão de unidades, prontidão do perfil (`UserReadiness`) e resumo de saúde.

## Responsabilidades

- Orquestrar a geração de resposta: `generate` (REST, não-streaming) e `generate_stream` (SSE, eventos `citation`/`token`/`done`/`error`)
- Aplicar guardrails de entrada (`check_input`) e saída (`check_output`) com respostas canônicas + `DISCLAIMER`
- Capturar automaticamente dados do paciente a partir da mensagem do médico (regex → LLM opcional → merge rules-win → persistir Patient + health logs)
- Selecionar o template de prompt conforme a prontidão do perfil do paciente: modo `normal` (completo), `focus` (primeira mensagem, só onboarding), `soft` (incompleto, lembrete curto)
- Recuperar contexto RAG (`search`) e resumo de saúde (`health_summary`) e injetar no system prompt
- Garantir o `DISCLAIMER` médico no final de toda resposta com viés clínico
- Prover fábrica de providers configurável via env `LLM_PROVIDER` (OpenAI/Gemini)
- Registrar eventos de auditoria (`GUARDRAIL_BLOCKED`, `MESSAGE_SENT`) via `record` — stub no MVP

## Regras de Negócio

- **RN-01** — Guardrail de entrada em ordem fixa: `URGENCY_PATTERNS` → `DIAGNOSIS_PATTERNS` → `PRESCRIPTION_PATTERNS` → `_is_gibberish`; o primeiro match vence e bloqueia. 🟢
- **RN-02** — Cada bloqueio de entrada tem `canned_reply` próprio (`URGENCY_REPLY`, `DIAGNOSIS_REPLY`, `PRESCRIPTION_REPLY`, `GIBBERISH_REPLY`); resposta bloqueada = canned_reply + `DISCLAIMER`, `tokens_used=0`, `blocked=True`. 🟢
- **RN-03** — Guardrail de saída: `FORBIDDEN_OUTPUT_PATTERNS` (ex.: "você tem câncer", "tome X mg", "o diagnóstico é") → resposta suprimida (REST: canned_reply + disclaimer; SSE: texto de supressão + `done blocked=True`). 🟢
- **RN-04** — Detecção de gibberish: normalização NFKD→ASCII→lower; palavra plausível se ≥3 chars com vogal e sem 6+ consoantes seguidas; texto com ≥3 palavras e <34% plausíveis → gibberish; repetição `(.)\1{6,}` → gibberish. 🟢
- **RN-05** — Seleção de prompt por prontidão: `is_complete` → modo normal; incompleto + 1ª mensagem → modo `focus` (só orienta registro dos dados faltantes, sem responder perguntas clínicas); incompleto + não-primeira → modo `soft` (responde + apêndice curto). 🟢
- **RN-06** — Captura rules-first: regex (`parse_rules`) têm precedência; LLM (`extract_with_llm`) só preenche `None`/gaps via `merge_extracted`. Desligável por env `DATA_CAPTURE_LLM=false`. 🟢
- **RN-07** — Prontidão mínima para `is_complete`: nome + `REQUIRED_PROFILE_FIELDS = (birth_date, biological_sex, height_cm)` + ao menos 1 `WeightLog`. 🟢
- **RN-08** — Disclaimer obrigatório (REST): se a resposta não termina com `DISCLAIMER`, é anexada. 🟢
- **RN-09** — Cada chunk RAG recuperado vira citação `{source, chunk_id}` e é injetado no system prompt com `(fonte: {source})`. 🟢
- **RN-10** — Gemini exige roles alternados: mensagens consecutivas do mesmo role são concatenadas no provider. 🟢
- **RN-11** — IMC: `bmi = round(kg/(m²), 2)`; categorias `<18.5` abaixo_do_peso, `<25` eutrofico, `<30` sobrepeso, `<35` obesidade_grau_1, `<40` obesidade_grau_2, senão grau_3; valida `weight_kg>0` e `height_cm>0`. 🟢
- **RN-12** — Conversão de unidades: `CONVERSIONS` (kg↔lb, cm↔in, ml↔fl_oz); par não suportado → `ValueError`. 🟢
- **RN-13** — `tokens_used` no streaming = `len(text.split())` (palavras, não tokens reais); no REST = `provider.usage.total_tokens`. 🟢 (imprecisão documentada)
- **RN-14** — `patient_created` no evento `done` do SSE nunca reporta `True` — `_ensure_patient` lê `getattr(result, "_patient_just_created", False)`, atributo inexistente em `CaptureResult`. 🟡
- **RN-15** — Guardrail bloqueado (entrada) registra `GUARDRAIL_BLOCKED` com `reason` e retorna `blocked=True`; saída bloqueada registra `output_<reason>`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Gerar resposta (REST) com guardrails de entrada e saída | Must | `generate(user_id, conv_id, query)` → `GenerateResult` com `content` (com `DISCLAIMER`), `tokens_used`, `blocked_by_guardrail`, `citations`, e opcionais `onboarding_mode`/`missing_basics`/`data_capture` |
| RF-02 | Gerar resposta em streaming (SSE) | Must | `generate_stream(...)` → `Iterator[dict]` emitindo `citation` (por chunk), `token` (por token), `done` (com metadados e `patient_id`/`patient_first_name`) ou `error` |
| RF-03 | Bloquear pedidos de diagnóstico | Must | Query "qual é o meu diagnóstico?" → `allowed=False`, reason `diagnosis`, `DIAGNOSIS_REPLY` |
| RF-04 | Bloquear pedidos de prescrição/medicação | Must | Query "que remédio devo tomar?" → `allowed=False`, reason `prescription`, `PRESCRIPTION_REPLY` |
| RF-05 | Bloquear relato de urgência | Must | Query "falta de ar / dor forte no peito" → `allowed=False`, reason `urgency`, `URGENCY_REPLY` |
| RF-06 | Bloquear gibberish | Must | Query "asdfghjk" → `allowed=False`, reason `gibberish`, `GIBBERISH_REPLY` |
| RF-07 | Guardrail de saída | Must | Resposta contendo "tome 500mg" → bloqueada com `blocked=True` e texto de supressão |
| RF-08 | Captura automática de dados do paciente | Must | Mensagem "Paciente João Silva, 80 kg, 1,75 m, dorme 6h" → cria/resolve `Patient`, persiste weight/sleep/profile, `CaptureResult.saved` preenchido |
| RF-09 | Onboarding focus na primeira mensagem com perfil incompleto | Should | 1ª mensagem + `is_complete=False` → prompt `ONBOARDING_FOCUS_TEMPLATE`, `onboarding_mode="focus"`, sem citações |
| RF-10 | Onboarding soft para perfil incompleto (não-primeira) | Should | Mensagem subsequente + `is_complete=False` → prompt normal + `ONBOARDING_SOFT_APPENDIX`, `onboarding_mode="soft"` |
| RF-11 | Injeção de contexto RAG e resumo de saúde | Must | `_build_messages` chama `search(query, RAG_TOP_K, RAG_MIN_SCORE)` e `health_summary(patient_id)`; contexto entra no `SYSTEM_PROMPT_TEMPLATE` |
| RF-12 | Provider configurável | Must | `LLM_PROVIDER=openai` → `OpenAIProvider`; `gemini` → `GeminiProvider`; outro → `RuntimeError` |
| RF-13 | Extração via LLM opcional | Could | `DATA_CAPTURE_LLM=false` → `_should_call_llm` retorna `False`; extração fica só regex |
| RF-14 | Skills auxiliares | Should | `calculate_bmi(weight_kg, height_cm)` → `{bmi, category}`; `convert_units(value, from, to)` → `{value, unit}`; `get_user_readiness(patient_id)` → `UserReadiness`; `health_summary(patient_id, window)` → `dict` |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | Nunca logar conteúdo de mensagens ou dados sensíveis — logs usam `user_id`, `conversation_id`, `reason`, sem PII | `apps/ai_engine/orchestrator.py:194,198,225,230,245` | 🟢 |
| Segurança | Respostas com viés clínico sempre acompanhadas de `DISCLAIMER` (guardrail de saída + anexo) | `apps/ai_engine/prompts.py:57-60`; `orchestrator.py:241-242` | 🟢 |
| Desempenho | `HISTORY_WINDOW` (env, default 6) limita o histórico carregado por turno | `orchestrator.py:27,81-83` | 🟢 |
| Desempenho | `MAX_TOKENS_PER_RESPONSE` (env, default 800) limita a saída do LLM | `orchestrator.py:28,215,298` | 🟢 |
| Desempenho | Extração LLM limitada a 400 tokens | `apps/ai_engine/services/data_extraction_llm.py:68` | 🟢 |
| Disponibilidade | Erros de provider viram `LLMProviderError` (502 no envelope REST; evento `error` no SSE) | `providers/openai_provider.py:29,40`; `providers/gemini_provider.py:53,67`; `orchestrator.py:301-303` | 🟢 |
| Privacidade | Extração de dados se limita ao que está explicitamente na mensagem (prompt instrutivo "Não invente dados") | `data_extraction_llm.py:20-43` | 🟢 |
| Observabilidade | Auditoria de `GUARDRAIL_BLOCKED` (entrada/saída) e `MESSAGE_SENT` (tokens + latência) via `record` — stub no MVP | `orchestrator.py:200,226,245-248` | 🟢 |

## Critérios de Aceitação

```gherkin
# Guardrail de entrada — diagnóstico
Dado a query "qual é o meu diagnóstico?"
Quando chamo generate(user_id, conv_id, query)
Então retorna GenerateResult com blocked_by_guardrail=True, tokens_used=0 e content = DIAGNOSIS_REPLY + DISCLAIMER

# Guardrail de entrada — urgência (prioridade sobre diagnóstico)
Dado a query "falta de ar e dor forte no peito, é infarto?"
Quando chamo check_input(query)
Então retorna allowed=False com reason="urgency" (URGENCY_PATTERNS testado antes de DIAGNOSIS)

# Guardrail de saída — resposta proibida
Dado content do LLM = "O paciente deve tomar 500mg de dipirona"
Quando chamo check_output(content)
Então retorna allowed=False com reason="forbidden_output"

# Gibberish
Dado a query "qwertyuiopasdfghjk"
Quando chamo check_input(query)
Então retorna allowed=False com reason="gibberish"

# Captura automática — happy path
Dado a mensagem do médico "Paciente João Silva, 80 kg, 1,75 m, dorme 6h/noite"
Quando chamo capture_from_message(conv_id, user_id, text)
Então result.saved contém name, profile(height_cm), weight_log e sleep_log; result.patient_id não é None

# Onboarding — primeira mensagem com perfil incompleto
Dado paciente com perfil incompleto e is_first_message=True
Quando chamo _resolve_messages(patient_id, conv_id, query, True)
Então retorna mensagens baseadas em ONBOARDING_FOCUS_TEMPLATE, onboarding_mode="focus" e sem citações

# Onboarding — perfil incompleto em mensagem posterior
Dado paciente com perfil incompleto e is_first_message=False
Quando chamo _resolve_messages(patient_id, conv_id, query, False)
Então retorna prompt normal + ONBOARDING_SOFT_APPENDIX e onboarding_mode="soft"

# Streaming — happy path
Dado um token válido e prompt liberado pelos guardrails
Quando itero generate_stream(user_id, conv_id, query)
Então recebo eventos citation (por chunk), token* e done com tokens_used, onboarding_mode, data_capture e patient_id

# Streaming — erro de provider
Dado que provider.stream lança exceção
Quando itero generate_stream(user_id, conv_id, query)
Então recebo evento {"type": "error", "code": "LLM_PROVIDER_ERROR"} e a iteração encerra

# Provider — desconhecido
Dado LLM_PROVIDER="anthropic"
Quando chamo get_provider()
Então levanta RuntimeError "Unknown LLM_PROVIDER: anthropic"

# IMC
Dado weight_kg=80 e height_cm=175
Quando chamo calculate_bmi(80, 175)
Então retorna {"bmi": 26.12, "category": "sobrepeso"}
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Geração REST + SSE (RF-01, RF-02) | Must | Núcleo da interação com a IA, consumido por `conversations` |
| Guardrails entrada/saída (RF-03 a RF-07) | Must | Restrição clínica inegociável (LGPD + segurança do paciente) |
| Captura automática (RF-08) | Must | Habilita o prontuário vivo e o onboarding |
| Injeção RAG + health summary (RF-11, RF-12) | Must | Contextualização das respostas |
| Onboarding focus/soft (RF-09, RF-10) | Should | Melhora completude do perfil, não bloqueia resposta |
| Skills auxiliares (RF-14) | Should | IMC/unit_convert sem uso direto no orquestrador hoje |
| Extração via LLM opcional (RF-13) | Could | Fallback de custo/privacidade; default ligado |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/ai_engine/orchestrator.py` | `generate`, `generate_stream`, `_resolve_messages`, `_build_messages`, `_build_onboarding_focus_messages`, `_load_history`, `_history_with_query`, `GenerateResult` | 🟢 |
| `apps/ai_engine/guardrails.py` | `check_input`, `check_output`, `_is_gibberish`, `_word_is_plausible`, `GuardrailResult`, padrões | 🟢 |
| `apps/ai_engine/prompts.py` | `SYSTEM_PROMPT_TEMPLATE`, `ONBOARDING_*`, `DATA_CAPTURE_SAVED_APPENDIX`, `CITATION_LINE`, `DISCLAIMER` | 🟢 |
| `apps/ai_engine/providers/__init__.py` | `get_provider` | 🟢 |
| `apps/ai_engine/providers/base.py` | `ChatMessage`, `LLMProvider` (Protocol) | 🟢 |
| `apps/ai_engine/providers/openai_provider.py` | `OpenAIProvider.stream/complete/complete_json` | 🟢 |
| `apps/ai_engine/providers/gemini_provider.py` | `GeminiProvider.stream/complete/complete_json`, `_build` | 🟢 |
| `apps/ai_engine/services/user_data_capture.py` | `capture_from_message`, `_ensure_patient`, `_persist_health_data` | 🟢 |
| `apps/ai_engine/services/capture_rules.py` | `parse_rules`, `has_actionable_data`, `message_likely_has_health_data` | 🟢 |
| `apps/ai_engine/services/capture_models.py` | `ExtractedUserData` + sub-modelos, `CaptureResult`, `_json_safe` | 🟢 |
| `apps/ai_engine/services/data_extraction_llm.py` | `extract_with_llm`, `merge_extracted`, `_should_call_llm`, `EXTRACTION_SYSTEM` | 🟢 |
| `apps/ai_engine/skills/user_readiness.py` | `get_user_readiness`, `UserReadiness`, `REQUIRED_PROFILE_FIELDS` | 🟢 |
| `apps/ai_engine/skills/health_summary.py` | `health_summary` | 🟢 |
| `apps/ai_engine/skills/bmi.py` | `calculate_bmi`, `BMIInput` | 🟢 |
| `apps/ai_engine/skills/unit_convert.py` | `convert_units`, `CONVERSIONS` | 🟢 |
| `apps/ai_engine/urls.py` | vazio (sem endpoints) | 🟢 |
| `apps/conversations/views.py` | consumidor: `generate` (POST) e `generate_stream` (SSE) | 🟡 |
| `config/settings.py` | env `HISTORY_WINDOW`, `MAX_TOKENS_PER_RESPONSE`, `RAG_TOP_K`, `RAG_MIN_SCORE` | 🟢 |

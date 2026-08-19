# AI Engine / Generate, Design Técnico

> Contrato operacional de **COMO** a geração é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `generate` | `(user_id: int, conversation_id: int, query: str, *, is_first_message: bool = False) -> GenerateResult` | `GenerateResult` (`orchestrator.py:183-258`) |
| `generate_stream` | `(user_id: int, conversation_id: int, query: str, *, is_first_message: bool = False) -> Iterator[dict]` | eventos `citation`/`token`/`done`/`error` (`orchestrator.py:261-348`) |

## Fluxo Principal

### 1. Geração REST — `generate`

1. `started = time.time()`; `pre = check_input(query)`. (`orchestrator.py:190-191`) 🟢
2. **Bloqueado na entrada:** loga `guardrail_blocked` (phase=input, reason, user_id, conversation_id), `record("GUARDRAIL_BLOCKED")`, retorna `GenerateResult(pre.canned_reply + "\n\n" + DISCLAIMER, 0, True, [])`. (`orchestrator.py:192-201`) 🟢
3. `capture_result = capture_from_message(...)`; `capture_meta = to_metadata()` **só se** `saved`/`errors` não-vazios, senão `None`. (`orchestrator.py:203-208`) 🟢
4. `_resolve_messages(...)` → `(messages, citations, onboarding_mode, missing_basics)`. (`orchestrator.py:210-213`) 🟢
5. `provider = get_provider()`; `content, tokens = provider.complete(messages, max_tokens=MAX_TOKENS)` (env `MAX_TOKENS_PER_RESPONSE`, default 800). (`orchestrator.py:214-215`, `orchestrator.py:28`) 🟢
6. **Bloqueado na saída:** `check_output(content)` falhou → loga `guardrail_blocked` (phase=output, reason=`output_<reason>`), `record("GUARDRAIL_BLOCKED")`, retorna canned reply + DISCLAIMER, `blocked=True`. (`orchestrator.py:217-239`) 🟢
7. `content` não termina com `DISCLAIMER` (após `strip()`) → anexa `\n\nDISCLAIMER`. (`orchestrator.py:241-242`) 🟢
8. `latency_ms`; `record("MESSAGE_SENT", metadata={tokens_used, blocked: False, latency_ms})`; retorna `GenerateResult(content, tokens, False, citations, onboarding_mode, missing_basics or still_missing, capture_meta)`. (`orchestrator.py:244-258`) 🟢

### 2. Geração streaming — `generate_stream`

1. `check_input(query)` bloqueia → `yield token(canned_reply + DISCLAIMER)`, `yield done(tokens_used=0, blocked=True)`, `return`. (`orchestrator.py:268-279`) 🟢
2. `capture_from_message` e `capture_meta` idênticos ao REST. (`orchestrator.py:281-286`) 🟢
3. `_resolve_messages(...)` → citações; **antes dos tokens**, `yield citation` por chunk RAG. (`orchestrator.py:289-294`) 🟢
4. `provider.stream(messages, max_tokens=MAX_TOKENS)` — acumula `full` e `yield token` por token. (`orchestrator.py:296-300`) 🟢
5. **Exceção no stream:** `yield error(LLM_PROVIDER_ERROR, str(e))`, `return`. (`orchestrator.py:301-303`) 🟢
6. `text = "".join(full)`; `check_output(text)`. Bloqueado → `yield token("\n\n[A resposta foi suprimida por política de segurança.]")` + `done(tokens_used=0, blocked=True, ...)`. (`orchestrator.py:305-327`) 🟢
7. **Liberado:** `done_payload` com `tokens_used = len(text.split())` (**palavras**), `blocked=False`, flags de onboarding/capture. (`orchestrator.py:329-336`) 🟢
8. Se `capture_result.patient_id`: injeta `patient_id`, `patient_created`, `patient_first_name` (fetch extra, falha silenciosa). (`orchestrator.py:337-348`) 🟢

## Fluxos Alternativos

- **[Mensagem sem dados de saúde]:** captura propaga patient_id + still_missing, sem persistir nem chamar LLM. 🟢
- **[Provider desconhecido]:** `RuntimeError` do factory sobe ao chamador. 🟢
- **[Falha ao buscar nome do paciente pós-stream]:** `except Exception: pass` — `patient_first_name` ausente no done, fluxo não quebra. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.ai_engine.guardrails.check_input/check_output` | Bloqueio de entrada/saída | `orchestrator.py:190,217,268,305` |
| `apps.ai_engine.services.user_data_capture.capture_from_message` | Captura automática | `orchestrator.py:203,281` |
| `apps.ai_engine.providers.get_provider` | Provider por env | `orchestrator.py:214,296` |
| `apps.ai_engine.prompts.DISCLAIMER` | Anexo de disclaimer | `orchestrator.py:241-242` |
| `apps.audit.services.log.record` | Auditoria (stub) | `GUARDRAIL_BLOCKED`, `MESSAGE_SENT` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| `MAX_TOKENS` e `HISTORY_WINDOW` lidos de env em module scope | `orchestrator.py:27-28` | 🟢 |
| `tokens_used`: REST `usage.total_tokens`; streaming conta palavras | `orchestrator.py:332` | 🟢 |
| `DISCLAIMER` anexado no REST, **não** no streaming | `orchestrator.py:241-242` vs `305-336` | 🟢 |
| Catch-all `except Exception` → `LLM_PROVIDER_ERROR` no stream | `orchestrator.py:301-303` | 🟢 |

## Riscos e Lacunas

- 🔴 `patient_created` nunca `True` no streaming — `getattr(result, "_patient_just_created", False)` lê atributo inexistente (`user_data_capture.py:124`).
- 🔴 `tokens_used` no streaming conta palavras — métricas imprecisas.
- 🔴 `DISCLAIMER` não é anexado no streaming — conformidade LGPD depende do LLM.
- 🔴 Catch-all no stream rotula qualquer erro como `LLM_PROVIDER_ERROR` — bugs internos mascarados.

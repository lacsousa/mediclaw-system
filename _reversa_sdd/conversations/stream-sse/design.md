# Conversations / Stream SSE, Design Técnico

> Contrato operacional de **COMO** o streaming SSE é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Revisado em 2026-08-19 após revisão cruzada — substitui símbolos e formato sup e corrige o fluxo real. [Revisão Codex]

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/conversations/<id>/stream/` | `?token=<jwt>&prompt=<str>` | `text/event-stream` (`data: {json}\n\n`) | 200, 400, 401, 404 | auth via `?token=` (sem throttle) |

## Fluxo Principal (`apps/conversations/views.py:120-264`) 🟢

1. View pura `stream(request, conv_id)` — sem DRF (`api_view`/`permission_classes`). (`views.py:120`) 🟢
2. Lê `token` e `prompt` do query string (`request.GET.get("token", "")`, `request.GET.get("prompt") or ""`). (`views.py:122-123`) 🟢
3. **Auth manual:** sem token → SSE `UNAUTHORIZED` 401; `AccessToken(token)` inválido ou user inexistente → SSE `UNAUTHORIZED` 401. (`views.py:125-151`) 🟢
4. Conversa escopada a `doctor=user`; senão → SSE `NOT_FOUND` 404. (`views.py:153-164`) 🟢
5. `prompt` vazio → SSE `VALIDATION_ERROR` 400. (`views.py:166-175`) 🟢
6. `conv.messages.count() >= MAX_MESSAGES` (constante `50` no views) → SSE `CONVERSATION_FULL` 400. (`views.py:177-186`) 🟢
7. `is_first = count == 0`; persiste Message USER; título auto-gerado (`prompt[:80]`) se vazio/`"Nova conversa"`. (`views.py:188-192`) 🟢
8. `generate_stream(user.id, conv.id, prompt, is_first_message)` itera eventos (`views.py:195-254`):
   - `token` → `full_content` acumulado (`{type: "token", content}`). 🟢
   - `citation` → `{type: "citation", source, chunk_id}`. 🟢
   - `done` → persiste Message ASSISTANT com `tokens_used`, `blocked_by_guardrail`, metadata (citations + onboarding/capture); `conv.save(update_fields=["updated_at"])`. (`views.py:221-245`) 🟢
   - `error` → loga warning (`stream_error`, `conversation_id`, sem conteúdo). (`views.py:246-252`) 🟢
   - Cada evento yield como `data: {json}\n\n`. (`views.py:253`) 🟢
9. Exceção inesperada → loga `stream_unexpected_error` e yield SSE `INTERNAL_ERROR`. (`views.py:255-260`) 🟢
10. Resposta com `Cache-Control: no-cache` e `X-Accel-Buffering: no`. (`views.py:262-264`) 🟢

## Fluxos Alternativos

- **[Token inválido/ausente]:** SSE `UNAUTHORIZED` 401 (não levanta exceção HTTP). 🟢
- **[Conversa inexistente/fora do escopo]:** SSE `NOT_FOUND` 404. 🟢
- **[Prompt vazio]:** SSE `VALIDATION_ERROR` 400. 🟢
- **[Limite de mensagens atingido]:** SSE `CONVERSATION_FULL` 400. 🟢
- **[Erro do LLM no meio do stream]:** evento `{"type": "error", "code": "LLM_PROVIDER_ERROR", "message": str(e)}` e encerra; a mensagem USER já persistida fica **órfã** (sem estado de turno). 🔴 (ver P-36)
- **[Guardrail de entrada bloqueia]:** o orquestrador emite `token(canned_reply + DISCLAIMER)` + `done(blocked=True)`; a mensagem ASSISTANT persistida carrega `blocked_by_guardrail=True`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.ai_engine.orchestrator` | Stream da geração | `generate_stream(user_id, conv_id, prompt, is_first_message)` (`views.py:195`) |
| `rest_framework_simplejwt.tokens.AccessToken` | Validar token do query param | `AccessToken(token)` → `token["user_id"]` (`views.py:137-141`) |
| `apps.ai_engine.prompts.DISCLAIMER` | Bloqueios de guardrail | via orquestrador (`canned_reply + DISCLAIMER`) |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| View pura Django (sem DRF) para streaming | `views.py:120` | 🟢 |
| Token via query param (`?token=`) — EventSource não envia headers | `views.py:122,136-141` | 🟢 |
| Erros via eventos SSE (não exceções HTTP) | `views.py:126-134,143-151,157-164,169-175,179-186` | 🟢 |
| Wire format `data: {json}\n\n` com `type` no JSON (sem linha `event:`) | `views.py:253` | 🟢 |
| Sem throttle no stream (apenas `post_message`) | `views.py:105` vs `views.py:120` | 🟢 |
| `MAX_MESSAGES=50` constante própria no views (env no service) | `views.py:22` vs `services/chat.py:7` | 🟢 (inconsistência 🟡) |

## Riscos e Lacunas

- 🔴 **Guardrail de saída pós-hoc (P-35):** o `check_output` do orquestrador roda **depois** de os tokens já terem sido transmitidos; conteúdo proibido pode chegar ao cliente antes da supressão. Invariante de guardrail não garantido no stream.
- 🔴 **DISCLAIMER ausente no caminho normal (P-22):** o stream liberado emite o texto cru do LLM, sem anexar o `DISCLAIMER`; conformidade LGPD depende do modelo.
- 🔴 **Turno órfão (P-36):** falha do provider, desconexão ou exceção após persistir a USER deixa mensagem sem resposta e sem estado `pending/failed`/idempotência/retry.
- 🔴 **Sem throttle (P-19):** caminho de maior custo (SSE) sem `ChatThrottle` — risco de custo e abuso.
- 🟡 **`MAX_MESSAGES` duplicado** (`50` hardcoded no views vs env `MAX_MESSAGES_PER_CONVERSATION` no service) — podem divergir se o env mudar (P-34).
- 🟡 **Token no query param** vaza em logs de acesso/proxy (permissions.md P3) — mitigar.

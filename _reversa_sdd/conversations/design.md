# Conversations, Design Técnico

> Contrato operacional de **COMO** a unit `conversations` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

### Endpoints HTTP

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/conversations/` | `page?` (int, default 1) | `{results, count, next}` | 200, 401 | `IsAuthenticated` |
| POST | `/api/v1/conversations/` | — | conversa criada (`{id, title, patient, created_at, updated_at}`) | 201, 401 | `IsAuthenticated` |
| GET | `/api/v1/conversations/<conv_id>/` | — | `{conversation, messages}` | 200, 401, 404 | `IsAuthenticated` |
| DELETE | `/api/v1/conversations/<conv_id>/` | — | `204 No Content` (soft-delete) | 204, 401, 404 | `IsAuthenticated` |
| POST | `/api/v1/conversations/<conv_id>/messages/` | `{content: str (1-4000)}` | mensagem ASSISTANT persistida | 201, 400, 401, 403, 404 | `IsAuthenticated` + `ChatThrottle` |
| GET | `/api/v1/conversations/<conv_id>/stream/` | `?token=<jwt>&prompt=<str>` | `text/event-stream` (SSE) | 200, 400, 401, 404 | auth via `?token=` |

Todos os recursos escopados a `doctor=request.user`. PUT/PATCH não são expostos (só GET/POST/DELETE por rota). 🟢

### Funções / classes

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `ChatThrottle` | `UserRateThrottle` (scope `chat`) | throttle | 10/min (settings) |
| `list_create` | `(request) -> Response` | conversa/lista | GET paginado manual; POST cria com título default |
| `detail` | `(request, conv_id: int) -> Response` | detalhe/204 | GET mensagens; DELETE soft-delete |
| `post_message` | `(request, conv_id: int) -> Response` | Message (201) | valida `CreateMessageInput`, chama `send_message` |
| `stream` | `(request, conv_id: int) -> StreamingHttpResponse` | SSE | auth via token, orquestrador `generate_stream` |
| `send_message` | `(user, conversation: Conversation, content: str) -> Message` | Message ASSISTANT | service não-HTTP, ownership + limite |
| `ensure_welcome_conversation` | `(user) -> Conversation \| None` | conversa | boas-vindas idempotente, `None` p/ ADMIN |

## Fluxo Principal

### 1. Listagem de conversas (`GET /api/v1/conversations/`)

1. `page = int(request.GET.get("page", 1))`, `offset = (page-1) * 20`. (`views.py:64-65`) 🟢
2. `Conversation.objects.filter(doctor=request.user).select_related("patient")` (manager `objects` exclui soft-deletadas). (`views.py:66`) 🟢
3. `total = qs.count()`; `items = qs[offset:offset+20]`; `has_next = offset+20 < total`. (`views.py:67-69`) 🟢
4. Serializa `{results, count, next}` (next = `?page=N+1` ou `null`). (`views.py:70-75`) 🟢

### 2. Criação de conversa (`POST /api/v1/conversations/`)

- `Conversation.objects.create(doctor=request.user, title="Nova conversa")` → 201. (`views.py:61`) 🟢

### 3. Detalhe com mensagens (`GET /api/v1/conversations/<id>/`)

1. Busca `Conversation.objects.select_related("patient").get(pk=conv_id, doctor=request.user)`; senão → 404 `NOT_FOUND`. (`views.py:82-87`) 🟢
2. `conv.messages.all()` (ordem `created_at`) e serializa `{conversation, messages}`. (`views.py:94-99`) 🟢

### 4. Soft-delete (`DELETE /api/v1/conversations/<id>/`)

1. Mesma busca escopada (404 se não pertence). (`views.py:82-87`) 🟢
2. `conv.deleted_at = timezone.now()`, `save(update_fields=["deleted_at"])` → 204. (`views.py:89-92`) 🟢

### 5. Envio de mensagem não-streaming (`POST .../messages/`)

1. Busca escopada (404). (`views.py:108-111`) 🟢
2. `CreateMessageInput` valida `content` (1–4000). (`views.py:113-114`; `serializers.py:32-33`) 🟢
3. `send_message(user, conv, content)`:
   - `conversation.doctor_id != user.id` → 403 `FORBIDDEN`. (`services/chat.py:11-12`) 🟢
   - `conversation.messages.count() >= MAX_MESSAGES` (env `MAX_MESSAGES_PER_CONVERSATION`, default 50) → 400 `CONVERSATION_FULL`. (`services/chat.py:13-14`) 🟢
   - `is_first = count == 0`. (`services/chat.py:16`) 🟢
   - `transaction.atomic()` cria Message USER. (`services/chat.py:18-19`) 🟢
   - `orchestrator.generate(...)` (IA) → monta `metadata.citations` + opcionais (`onboarding_mode`, `missing_basics`, `data_capture`). (`services/chat.py:21-35`) 🟡 (chamada LLM externa)
   - Cria Message ASSISTANT (content, `tokens_used`, `blocked_by_guardrail`, metadata) e atualiza `updated_at`. (`services/chat.py:36-44`) 🟢
4. Retorna 201 com `MessageSerializer(msg).data`. (`views.py:116-117`) 🟢

### 6. Streaming SSE (`GET .../stream/`)

1. Lê `token` e `prompt` do query string. (`views.py:122-123`) 🟢
2. **Auth manual:** sem token → SSE `UNAUTHORIZED` 401; `AccessToken(token)` inválido ou user inexistente → SSE `UNAUTHORIZED` 401. (`views.py:125-151`) 🟢
3. Conversa escopada a `doctor=user`; senão → SSE `NOT_FOUND` 404. (`views.py:153-164`) 🟢
4. `prompt` vazio → SSE `VALIDATION_ERROR` 400. (`views.py:166-175`) 🟢
5. `conv.messages.count() >= MAX_MESSAGES` → SSE `CONVERSATION_FULL` 400. (`views.py:177-186`) 🟢
6. `is_first = count == 0`; persiste Message USER; título auto-gerado (`prompt[:80]`) se vazio/`"Nova conversa"`. (`views.py:188-192`) 🟢
7. `generate_stream(user.id, conv.id, prompt, is_first_message)` itera eventos:
   - `token` → acumula `full_content`. (`views.py:212-214`) 🟢
   - `citation` → acumula `{source, chunk_id}`. (`views.py:215-220`) 🟢
   - `done` → persiste Message ASSISTANT com `tokens_used`, `blocked_by_guardrail`, metadata (citations + onboarding/capture), `conv.save(update_fields=["updated_at"])`. (`views.py:221-245`) 🟢
   - `error` → loga warning (`stream_error`, `conversation_id`, sem conteúdo). (`views.py:246-252`) 🟢
   - Cada evento é yield como `data: {json}\n\n`. (`views.py:253`) 🟢
8. Exceção inesperada → loga `stream_unexpected_error` e yield SSE `INTERNAL_ERROR`. (`views.py:255-260`) 🟢
9. Resposta com `Cache-Control: no-cache` e `X-Accel-Buffering: no`. (`views.py:262-264`) 🟢

## Fluxos Alternativos

- **[Sem `page` na listagem]:** `page=1` (default). 🟢
- **[Soft-deletada na listagem]:** excluída (manager `ActiveConversationManager`). 🟢
- **[Conversa de outro médico]:** 404 `NOT_FOUND` (HTTP) / 403 `FORBIDDEN` (service `send_message`). 🟢
- **[Limite de mensagens atingido]:** 400 `CONVERSATION_FULL` no POST; SSE `CONVERSATION_FULL` no streaming. 🟢
- **[Token inválido no stream]:** SSE `UNAUTHORIZED` 401 (não levanta exceção HTTP). 🟢
- **[Erro do orquestrador de IA]:** evento `error` logado; fluxo continua o SSE; falha interna vira SSE `INTERNAL_ERROR`. 🟡

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.patients.models.Patient` | Vínculo opcional da conversa | FK `SET_NULL`, `related_name="conversations"` (`models.py:18-24`) |
| `settings.AUTH_USER_MODEL` | Dono da conversa | FK `CASCADE`, `related_name="conversations"` (`models.py:13-17`) |
| `apps.ai_engine.orchestrator` | Geração da resposta | `generate` (POST) e `generate_stream` (SSE) (`services/chat.py:21`; `views.py:195`) |
| `apps.ai_engine.prompts.DISCLAIMER` | Mensagem de boas-vindas | `WELCOME_MESSAGE` concatena o disclaimer (`services/welcome.py:19`) |
| `apps.common.exceptions.AppError` | Erros com envelope | `NOT_FOUND`, `FORBIDDEN`, `CONVERSATION_FULL` (`views.py:87,111`; `services/chat.py:12,14`) |
| `rest_framework_simplejwt.tokens.AccessToken` | Auth do streaming | Valida `?token=` e extrai `user_id` (`views.py:137-141`) |
| `rest_framework.throttling.UserRateThrottle` | Throttle de chat | `ChatThrottle` com scope `chat` (`views.py:25-26`) |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Soft-delete de conversa (não hard delete), com manager default filtrando | `models.py:5-9,28,30-31`; `views.py:90-92` | 🟢 |
| Streaming autenticado por `?token=` em vez de header (EventSource não envia headers) | `views.py:120-122,136-141` | 🟢 |
| Listagem com paginação manual (offset/limit) em vez de `DefaultPagination` global | `views.py:64-75` | 🟢 |
| Serialização manual com dicts (`_serialize_conversation`/`_serialize_message`) em vez de DRF serializers na listagem | `views.py:29-54` | 🟢 |
| `MAX_MESSAGES` duplicado: `PAGE_SIZE`/`MAX_MESSAGES=50` hardcoded no views + env no service | `views.py:21-22`; `services/chat.py:7` | 🟢 (inconsistência 🟡) |
| `patient` opcional (`SET_NULL`) — vínculo feito pela captura automática no chat | `models.py:18-24` | 🟢 |
| Boas-vindas como conversa real com mensagem estática (sem LLM), idempotente por título | `services/welcome.py:23-50` | 🟢 |
| Mensagem USER criada dentro de `transaction.atomic()` antes do LLM | `services/chat.py:18-19` | 🟢 |
| Resposta ASSISTANT traz metadata JSON com citações e flags de onboarding | `models.py:51`; `services/chat.py:28-35`; `views.py:230-244` | 🟢 |
| Erros do stream via eventos SSE (não exceções HTTP) | `views.py:126-134,143-151,157-164,169-175,179-186` | 🟢 |

## Estado Interno

| Modelo | Campos | Ordenação / índice |
|--------|--------|--------------------|
| `Conversation` | `doctor` FK, `patient` FK (nullable, SET_NULL), `title` Char(200), `created_at`, `updated_at`, `deleted_at` | `-updated_at`; índices `(doctor, -updated_at)`, `(patient, -updated_at)` |
| `Message` | `conversation` FK (CASCADE), `role` (USER/ASSISTANT/SYSTEM), `content` Text, `tokens_used` (nullable), `blocked_by_guardrail` Bool, `metadata` JSON (default `{}`), `created_at` | `created_at`; índice `(conversation, created_at)` |

`Conversation.objects` = manager ativo (filtra `deleted_at__isnull=True`); `Conversation.all_objects` = todos (inclui soft-deletadas). 🟢
`Message.conversation` `on_delete=CASCADE` → apagar conversa remove mensagens (LGPD/soft-delete mantém até retenção). 🟢

## Observabilidade

- Logs estruturados via `get_logger(__name__)` com eventos `stream_error` e `stream_unexpected_error`, contendo apenas `conversation_id` e evento — **nunca** `Message.content` (PII). 🟢
- `send_message` (POST não-streaming) não loga erros de LLM — exceção sobe ao DRF handler. 🟡
- Sem métricas de latência/tokens por conversa (apenas `tokens_used` persistido no model). 🟡
- Throttle `chat` 10/min ativo (limite implícito, sem observabilidade de rejeição). 🟢

## Riscos e Lacunas

- 🔴 Inconsistência de código de erro de limite: views usa `CONVERSATION_FULL` no SSE, service usa `CONVERSATION_FULL`, mas o PROJECT-CONTEXT documenta `CONVERSATION_LIMIT_REACHED` — definir qual é o canônico e alinhar.
- 🔴 `MAX_MESSAGES` duplicado: hardcoded `50` em `views.py:22` e env `MAX_MESSAGES_PER_CONVERSATION` em `services/chat.py:7` — podem divergir se o env mudar.
- 🔴 `except (TokenError, Exception)` no stream é catch-all — qualquer erro ao decodificar o token cai como `UNAUTHORIZED`, sem diagnóstico.
- 🟡 `_serialize_patient` expõe `first_name` de um possível paciente não vinculado — validar se isso vaza dado de paciente de outro contexto.
- 🟡 `send_message` cria a mensagem USER antes da chamada LLM sem rollback: se o LLM falhar, fica uma mensagem USER órfã sem resposta.
- 🟡 Retenção LGPD de 90 dias (PROJECT-CONTEXT) não implementada: soft-deleted nunca são expurgadas pelo módulo.
- 🟡 Role `SYSTEM` definido no modelo mas sem produtor no código do módulo — confirmar se a camada de IA a cria.

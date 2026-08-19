# Conversations, Tarefas de Implementação

> Sequência executável para reimplementar a unit `conversations` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Unit `accounts` implementada (`AUTH_USER_MODEL` com role, ex.: `doctor`/`ADMIN`)
- [ ] Unit `patients` implementada (FK `patient` aponta para `patients.Patient`)
- [ ] Unit `common` implementada (`AppError`, renderer de envelope, `get_logger` em `apps/common/logging_config.py`)
- [ ] Unit `ai_engine` com `orchestrator.generate` e `generate_stream` e `prompts.DISCLAIMER` (dependência de runtime do chat)
- [ ] Variáveis de ambiente: `MAX_MESSAGES_PER_CONVERSATION` (default 50), throttle `chat` configurado em settings
- [ ] Schema PostgreSQL criado e migrations aplicadas

## Tarefas

- [ ] **T-01**, Modelo `Conversation` com soft-delete e managers duplos
  - Origem no legado: `apps/conversations/models.py:5-38`
  - Critério de pronto: migration cria `Conversation` com `doctor` FK (`CASCADE`, `related_name="conversations"`), `patient` FK (`SET_NULL`, null/blank, `related_name="conversations"`), `title` Char(200) blank default `""`, `created_at`/`updated_at` (auto), `deleted_at` null; `ActiveConversationManager` filtra `deleted_at__isnull=True` como `objects`, `all_objects` = manager padrão; ordering `-updated_at`; índices `(doctor, -updated_at)` e `(patient, -updated_at)`
  - Confiança: 🟢

- [ ] **T-02**, Modelo `Message` com roles e metadata JSON
  - Origem no legado: `apps/conversations/models.py:41-58`
  - Critério de pronto: migration cria `Message` com `conversation` FK (`CASCADE`, `related_name="messages"`), `role` Char(10) choices USER/ASSISTANT/SYSTEM, `content` Text, `tokens_used` PositiveInt null, `blocked_by_guardrail` Bool default False, `metadata` JSON default `dict`, `created_at` auto; ordering `created_at`; índice `(conversation, created_at)`
  - Confiança: 🟢

- [ ] **T-03**, Serializers (`MessageSerializer`, `ConversationSerializer`, `CreateMessageInput`)
  - Origem no legado: `apps/conversations/serializers.py:5-33`
  - Critério de pronto: `MessageSerializer` com fields `[id, role, content, tokens_used, blocked_by_guardrail, metadata, created_at]`; `ConversationSerializer` com `[id, title, created_at, updated_at]`; `ConversationDetailSerializer` herda e adiciona `messages` (many, read_only); `CreateMessageInput` (Serializer) valida `content` com `min_length=1, max_length=4000`
  - Confiança: 🟢

- [ ] **T-04**, Helpers de serialização manual (`_serialize_patient`, `_serialize_conversation`, `_serialize_message`)
  - Origem no legado: `apps/conversations/views.py:29-54`
  - Critério de pronto: `_serialize_patient` retorna `None` se paciente nulo, senão `{id, first_name}`; `_serialize_conversation` retorna `{id, title, patient, created_at, updated_at}` com timestamps em isoformat; `_serialize_message` retorna `{id, role, content, tokens_used, blocked_by_guardrail, metadata, created_at}`
  - Confiança: 🟢

- [ ] **T-05**, Listagem e criação (`list_create`)
  - Origem no legado: `apps/conversations/views.py:57-76`
  - Critério de pronto: GET → paginação manual (`PAGE_SIZE=20`, `page` query param default 1, `offset`, `has_next`), queryset `filter(doctor=request.user).select_related("patient")` com `count` e `next` (`?page=N+1` ou `null`); POST → cria com `title="Nova conversa"` → 201; `@api_view(["GET", "POST"])` + `@permission_classes([IsAuthenticated])`
  - Confiança: 🟢

- [ ] **T-06**, Detalhe e soft-delete (`detail`)
  - Origem no legado: `apps/conversations/views.py:79-100`
  - Critério de pronto: busca `select_related("patient").get(pk=conv_id, doctor=request.user)`; `DoesNotExist` → `AppError("NOT_FOUND", ..., 404)`; GET → `{conversation, messages}` (todas as mensagens em ordem `created_at`); DELETE → seta `deleted_at=timezone.now()`, `save(update_fields=["deleted_at"])` → 204
  - Confiança: 🟢

- [ ] **T-07**, Envio de mensagem não-streaming (`post_message`)
  - Origem no legado: `apps/conversations/views.py:103-117`
  - Critério de pronto: busca escopada (404); `CreateMessageInput` valida; chama `send_message(user, conv, content)`; responde 201 com `MessageSerializer(msg).data`; decorado com `@throttle_classes([ChatThrottle])`
  - Confiança: 🟢

- [ ] **T-08**, Service `send_message` com ownership, limite e transação
  - Origem no legado: `apps/conversations/services/chat.py:10-45`
  - Critério de pronto: `MAX_MESSAGES` lido de env `MAX_MESSAGES_PER_CONVERSATION` (default 50); `doctor_id != user.id` → `AppError("FORBIDDEN", ..., 403)`; `count >= MAX_MESSAGES` → `AppError("CONVERSATION_FULL", ..., 400)`; cria Message USER em `transaction.atomic()`; chama `orchestrator.generate`; monta `metadata.citations` (`{source, chunk_id}`) + opcionais `onboarding_mode`/`missing_basics`/`data_capture`; cria Message ASSISTANT (content, `tokens_used`, `blocked_by_guardrail`, metadata); atualiza `conv.updated_at`; retorna a mensagem
  - Confiança: 🟢

- [ ] **T-09**, Streaming SSE com auth via token (`stream`)
  - Origem no legado: `apps/conversations/views.py:120-265`
  - Critério de pronto: `StreamingHttpResponse` com `content_type="text/event-stream"`; valida `?token=` via `AccessToken` + `User.objects.get(id=token["user_id"])` (ausente/inválido → SSE `UNAUTHORIZED` 401); conversa escopada a `doctor=user` (senão SSE `NOT_FOUND` 404); prompt vazio → SSE `VALIDATION_ERROR` 400; `count >= MAX_MESSAGES` → SSE `CONVERSATION_FULL` 400; persiste Message USER; título auto-gerado `prompt[:80]` se vazio/`"Nova conversa"`; itera `generate_stream` e yield `data: {json}\n\n` por evento (`token`/`citation`/`done`/`error`); no `done` persiste Message ASSISTANT com metadata e `conv.save(update_fields=["updated_at"])`; exceção → loga `stream_unexpected_error` e yield SSE `INTERNAL_ERROR`; headers `Cache-Control: no-cache`, `X-Accel-Buffering: no`
  - Confiança: 🟢

- [ ] **T-10**, Service `ensure_welcome_conversation` (boas-vindas idempotente)
  - Origem no legado: `apps/conversations/services/welcome.py:23-50`
  - Critério de pronto: retorna `None` para usuário com `role == "ADMIN"`; busca `Conversation.all_objects.filter(doctor_id=user.id, title="Bem-vindo")` (inclui soft-deletadas) e retorna se existir; senão cria conversa `title="Bem-vindo"` + Message ASSISTANT com `WELCOME_MESSAGE` (que concatena `DISCLAIMER`), `tokens_used=0`, `blocked_by_guardrail=False`, `metadata={"welcome": True}`
  - Confiança: 🟢

- [ ] **T-11**, Rotas da unit
  - Origem no legado: `apps/conversations/urls.py:5-10`
  - Critério de pronto: `""` → `list_create`, `<int:conv_id>/` → `detail`, `<int:conv_id>/messages/` → `post_message`, `<int:conv_id>/stream/` → `stream`; montado em `api/v1/conversations/`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Listagem: 25 conversas → página 2 com 5 itens, `count=25`, `next="?page=3"`; última página `next=null`
- [ ] **TT-02**, Criação: POST → 201 com `title="Nova conversa"` e timestamps isoformat
- [ ] **TT-03**, Detalhe: conversa com 3 mensagens → `messages` em ordem `created_at`
- [ ] **TT-04**, Soft-delete: DELETE → 204; conversa some da listagem mas aparece em `all_objects` com `deleted_at` preenchido
- [ ] **TT-05**, Ownership: conversa de outro médico → 404 `NOT_FOUND` no detail/delete/messages/stream
- [ ] **TT-06**, POST message: content válido → 201 com Message ASSISTANT e `metadata.citations`
- [ ] **TT-07**, POST message inválido: content vazio ou > 4000 → 400
- [ ] **TT-08**, Limite: 50 mensagens → nova tentativa → 400 `CONVERSATION_FULL` (POST) e SSE `CONVERSATION_FULL`
- [ ] **TT-09**, Stream sem token → 401 SSE `UNAUTHORIZED`; token inválido → 401
- [ ] **TT-10**, Stream com prompt vazio → 400 SSE `VALIDATION_ERROR`
- [ ] **TT-11**, Stream happy path: eventos `token`/`citation`/`done`; USER e ASSISTANT persistidos; título auto-gerado dos primeiros 80 chars do prompt
- [ ] **TT-12**, Stream erro de LLM: mock `generate_stream` lança → SSE `INTERNAL_ERROR` e log `stream_unexpected_error` sem conteúdo da mensagem
- [ ] **TT-13**, `send_message` service: médico diferente → 403 `FORBIDDEN`
- [ ] **TT-14**, `ensure_welcome_conversation`: ADMIN → `None`; não-ADMIN → conversa `"Bem-vindo"` criada com metadata `{welcome: true}`; chamada repetida não duplica
- [ ] **TT-15**, Cascade: deletar usuário remove conversas e mensagens

## Tarefas de Migração de Dados (se aplicável)

- n/a — reimplementação do schema a partir do zero. 🟡

## Ordem Sugerida

1. T-01 → T-02 (modelos) + T-11 (rotas) primeiro: base da unit.
2. T-03 (serializers) e T-04 (helpers de serialização) — dependem dos modelos.
3. T-05 → T-07 (views) — dependem dos modelos e do `send_message`.
4. T-08 (service `send_message`) e T-09 (streaming) — dependem de `ai_engine.orchestrator` (mockar LLM nos testes); T-09 depende de `common.logging_config.get_logger`.
5. T-10 (boas-vindas) — depende de `ai_engine.prompts.DISCLAIMER`.
6. Testes TT-01 a TT-07 (HTTP) após views; TT-08 a TT-13 (limite/stream/service) após services; TT-14 (welcome) e TT-15 (cascade) por último.

## Lacunas Pendentes (🔴)

- [ ] Definir o código canônico de limite de mensagens: código usa `CONVERSATION_FULL`, PROJECT-CONTEXT documenta `CONVERSATION_LIMIT_REACHED` — alinhar com o frontend e a doc.
- [ ] Unificar `MAX_MESSAGES`: hardcoded `50` em `views.py:22` vs env `MAX_MESSAGES_PER_CONVERSATION` em `services/chat.py:7` — decidir fonte única.
- [ ] `except (TokenError, Exception)` no stream é catch-all — refinar para não mascarar erros reais de decodificação.
- [ ] Retenção LGPD de 90 dias não implementada — decidir mecanismo de expurgo de conversas soft-deletadas.
- [ ] Comportamento com mensagem USER órfã quando o LLM falha (sem rollback) — decidir se reverter ou manter para retry.

# Conversations — Requisitos

> Contrato operacional da unit `conversations` (histórico de chat com a IA).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Módulo de conversas entre médico e IA: CRUD de conversas (com soft-delete), mensagens com roles, envio de mensagens via POST (não-streaming) e via SSE streaming com autenticação por `?token=` (EventSource não envia headers), limite de 50 mensagens por conversa, e conversa de boas-vindas automática para médicos recém-cadastrados (mensagem estática, sem LLM).

## Responsabilidades

- Listar/criar conversas do médico autenticado, com paginação manual de 20 itens
- Exibir detalhe da conversa com todas as mensagens (ordenadas por `created_at`)
- Soft-delete de conversa (seta `deleted_at`, não remove do banco)
- Enviar mensagem e obter resposta da IA via POST (`/messages/`) e via SSE streaming (`/stream/`)
- Aplicar limite de 50 mensagens por conversa
- Garantir ownership: conversas são escopadas ao `doctor=request.user` (404 se não pertence; 403 no service)
- Autenticar o streaming via `?token=` JWT (AccessToken) — sem header de autorização
- Criar conversa de boas-vindas idempotente para médico cadastrado (exceto ADMIN)

## Regras de Negócio

- **RN-01** — Conversa pertence a um `doctor` via FK `on_delete=CASCADE`; mensagens removidas em cascata com a conversa. 🟢
- **RN-02** — Soft-delete: `deleted_at` preenchido com `timezone.now()`; manager padrão (`objects`) exclui soft-deletadas, `all_objects` as inclui. 🟢
- **RN-03** — Ownership no HTTP: busca sempre filtrada por `doctor=request.user`; fora do escopo → 404 `NOT_FOUND`. 🟢
- **RN-04** — Ownership no service: `conversation.doctor_id != user.id` → 403 `FORBIDDEN`. 🟢
- **RN-05** — Limite de mensagens: `MAX_MESSAGES` de `MAX_MESSAGES_PER_CONVERSATION` (env, default 50); excedido → `CONVERSATION_FULL` (service) / `CONVERSATION_FULL` no SSE. 🟢
- **RN-06** — `patient` da conversa é FK `SET_NULL` (opcional) — paciente pode ser vinculado posteriormente pela captura automática. 🟢
- **RN-07** — Título auto-gerado: se vazio ou `"Nova conversa"`, recebe os primeiros 80 chars do primeiro prompt. 🟢
- **RN-08** — Criação via POST gera título padrão `"Nova conversa"`. 🟢
- **RN-09** — `CreateMessageInput` valida `content` com 1–4000 chars. 🟢
- **RN-10** — Streaming autenticado por `?token=` (AccessToken JWT); ausente/inválido → evento SSE de erro `UNAUTHORIZED` com status 401. 🟢
- **RN-11** — Streaming: prompt vazio → SSE `VALIDATION_ERROR` 400; conversa inexistente → SSE `NOT_FOUND` 404. 🟢
- **RN-12** — Mensagem `SYSTEM` é role permitida no modelo, mas não é criada por este módulo (vem da camada de IA). 🟡
- **RN-13** — Throttle específico de chat (`scope="chat"`, 10/min) aplicado **apenas** a `post_message`; o `stream` SSE não tem throttle (lacuna de custo/segurança). Defaults globais `anon` 30/min e `user` 60/min. 🟢 [Revisão Codex]
- **RN-14** — Conversa de boas-vindas: criada para médico (não-ADMIN), título `"Bem-vindo"`, mensagem ASSISTANT estática com `DISCLAIMER`, `tokens_used=0`, metadata `{welcome: true}`; idempotente por título. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Listar conversas paginadas do médico | Must | GET `/api/v1/conversations/?page=N` → `{results, count, next}`; `PAGE_SIZE=20`; conversas soft-deletadas ausentes |
| RF-02 | Criar conversa | Must | POST `/api/v1/conversations/` → 201 com título `"Nova conversa"` |
| RF-03 | Detalhe da conversa com mensagens | Must | GET `/api/v1/conversations/<id>/` → `{conversation, messages}` ordenadas por `created_at` |
| RF-04 | Soft-delete de conversa | Must | DELETE `/api/v1/conversations/<id>/` → 204; conversa some da listagem, mas permanece no banco (`all_objects`) |
| RF-05 | Enviar mensagem (não-streaming) | Must | POST `/api/v1/conversations/<id>/messages/` com `{content}` → 201 com a mensagem ASSISTANT persistida |
| RF-06 | Streaming SSE com auth por token | Must | GET `/api/v1/conversations/<id>/stream/?token=<jwt>&prompt=...` → `text/event-stream`, eventos `token`/`citation`/`done`; mensagens USER e ASSISTANT persistidas |
| RF-07 | Limite de mensagens | Must | Conversa com 50 mensagens + nova tentativa → erro `CONVERSATION_FULL` (400 no POST; SSE `CONVERSATION_FULL`) |
| RF-08 | Ownership escopada | Must | Acessar conversa de outro médico → 404 `NOT_FOUND` (HTTP) / 403 `FORBIDDEN` (service) |
| RF-09 | Conversa de boas-vindas no cadastro | Should | `ensure_welcome_conversation(user)` → cria conversa `"Bem-vindo"` com mensagem estática; retorna `None` para ADMIN; não duplica em chamada repetida |
| RF-10 | Metadata de citações/onboarding na mensagem ASSISTANT | Should | Mensagem ASSISTANT persistida com `metadata.citations` (e `onboarding_mode`, `missing_basics`, `data_capture` quando presentes) |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | `IsAuthenticated` em todas as rotas HTTP | `apps/conversations/views.py:58,80,104` | 🟢 |
| Segurança | Auth do streaming via `?token=` (AccessToken JWT) validado com `token["user_id"]` | `apps/conversations/views.py:122-141` | 🟢 |
| Segurança | Ownership escopado por `doctor=request.user` / `doctor=user` | `apps/conversations/views.py:66,84,109,154` | 🟢 |
| Desempenho | Streaming com `X-Accel-Buffering: no` e `Cache-Control: no-cache` (proxies) | `apps/conversations/views.py:263-264` | 🟢 |
| Desempenho | Índices `(doctor, -updated_at)` e `(patient, -updated_at)` em `Conversation`; `(conversation, created_at)` em `Message` | `apps/conversations/models.py:35-38,56-58` | 🟢 |
| Disponibilidade | Throttling de chat 10/min (`ChatThrottle`, scope `chat`) **somente em `post_message`** — `stream` sem throttle | `apps/conversations/views.py:105` (stream: `views.py:120` sem decorator); `config/settings.py:127` | 🟢 [Revisão Codex] |
| Privacidade | `Message.content` nunca logada; logs usam apenas `conversation_id` e evento (sem PII) | `apps/conversations/views.py:247-260` | 🟢 |
| Integridade | Mensagem USER persistida em transação antes da chamada ao orquestrador | `apps/conversations/services/chat.py:18-19` | 🟢 |

## Critérios de Aceitação

```gherkin
# Listagem — happy path
Dado um médico autenticado com 25 conversas ativas
Quando faço GET em /api/v1/conversations/?page=2
Então recebo 200 com 5 itens, count=25 e next="?page=3"

# Listagem — soft-delete exclui
Dado uma conversa com deleted_at preenchido
Quando faço GET em /api/v1/conversations/
Então a conversa não aparece na lista (manager padrão filtra)

# Criação
Quando faço POST em /api/v1/conversations/
Então recebo 201 com título "Nova conversa"

# Detalhe — ownership
Dado uma conversa de outro médico
Quando faço GET em /api/v1/conversations/<id>/
Então recebo 404 NOT_FOUND

# Soft-delete
Quando faço DELETE em /api/v1/conversations/<id>/
Então recebo 204 e a conversa permanece via all_objects com deleted_at preenchido

# Envio de mensagem — sem streaming
Dado uma conversa com menos de 50 mensagens e content válido
Quando faço POST em /api/v1/conversations/<id>/messages/
Então recebo 201 com a mensagem ASSISTANT (role, content, tokens_used, metadata.citations)

# Envio — limite atingido
Dado uma conversa com 50 mensagens
Quando tento POST em /api/v1/conversations/<id>/messages/
Então recebo 400 CONVERSATION_FULL

# Streaming — token ausente
Quando faço GET em /api/v1/conversations/<id>/stream/?prompt=oi
Então recebo 401 com evento SSE {"type": "error", "code": "UNAUTHORIZED"}

# Streaming — prompt vazio
Dado um token válido
Quando faço GET em /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=
Então recebo 400 com evento SSE {"type": "error", "code": "VALIDATION_ERROR"}

# Streaming — happy path
Dado um token válido e prompt preenchido
Quando faço GET em /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=oi
Então recebo SSE com eventos token, citation e done; mensagens USER e ASSISTANT persistidas; título auto-gerado dos primeiros 80 chars

# Boas-vindas
Dado um médico recém-cadastrado (não-ADMIN)
Quando chamo ensure_welcome_conversation(user)
Então uma conversa "Bem-vindo" é criada com mensagem estática; chamada repetida retorna a mesma (idempotente)
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| CRUD de conversas + soft-delete (RF-01 a RF-04) | Must | Caminho crítico de histórico do chat |
| Envio de mensagem e streaming (RF-05, RF-06, RF-10) | Must | Núcleo da interação com a IA |
| Limite e ownership (RF-07, RF-08) | Must | Integridade e privacidade (dados sensíveis de saúde) |
| Boas-vindas (RF-09) | Should | Melhora o onboarding, mas não bloqueia o uso |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/conversations/models.py` | `Conversation`, `ActiveConversationManager`, `Message` | 🟢 |
| `apps/conversations/views.py` | `list_create`, `detail`, `post_message`, `stream`, `ChatThrottle` | 🟢 |
| `apps/conversations/serializers.py` | `MessageSerializer`, `ConversationSerializer`, `ConversationDetailSerializer`, `CreateMessageInput` | 🟢 |
| `apps/conversations/services/chat.py` | `send_message` | 🟢 |
| `apps/conversations/services/welcome.py` | `ensure_welcome_conversation`, `WELCOME_MESSAGE` | 🟢 |
| `apps/conversations/urls.py` | rotas `""`, `<id>/`, `<id>/messages/`, `<id>/stream/` | 🟢 |
| `apps/ai_engine/orchestrator.py` | `generate_stream`, `generate` (dependência externa) | 🟡 |
| `config/settings.py` | throttle rates (`chat` 10/min), paginação | 🟢 |

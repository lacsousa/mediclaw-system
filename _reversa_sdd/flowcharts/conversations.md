# Fluxogramas — conversations

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. List / Create (GET/POST `/api/v1/conversations/`)

```mermaid
flowchart TD
    A[Request autenticado] --> B{GET ou POST?}
    B -- GET --> C[qs = Conversation.objects.filter doctor=request.user, select_related patient]
    C --> D[total = qs.count]
    D --> E[offset = page-1 * 20]
    E --> F[items = qs offset:offset+20]
    F --> G{offset+20 < total?}
    G -- sim --> H[next = ?page=n+1]
    G -- não --> I[next = null]
    H --> J[200 results, count, next]
    I --> J
    B -- POST --> K[Conversation.create doctor=request.user, title=Nova conversa]
    K --> L[201 id, title, patient null, timestamps]
```

> Resposta envolta pelo `EnvelopeJSONRenderer` → `{data: {...}, error: null, meta: {}}`. 🟢

## 2. Detail / Delete (GET/DELETE `/api/v1/conversations/<id>/`)

```mermaid
flowchart TD
    A[Request autenticado] --> B{GET ou DELETE?}
    B -- GET --> C[get pk=id, doctor=request.user]
    C -- não existe --> C1[404 NOT_FOUND]
    C -- existe --> D[messages = conv.messages.all]
    D --> E[200 conversation + messages]
    B -- DELETE --> F[get pk=id, doctor=request.user]
    F -- não existe --> F1[404 NOT_FOUND]
    F -- existe --> G[conv.deleted_at = now, save update_fields deleted_at]
    G --> H[204]
```

> Soft delete: a linha some de `Conversation.objects` (manager exclui `deleted_at IS NOT NULL`), mas continua em `Conversation.all_objects`. 🟢

## 3. Post message (POST `/api/v1/conversations/<id>/messages/`)

```mermaid
flowchart TD
    A[Request autenticado + ChatThrottle 10/min] --> B[get pk, doctor=request.user]
    B -- não existe --> B1[404 NOT_FOUND]
    B -- existe --> C[CreateMessageInput valida content 1-4000]
    C -- inválido --> C1[400 VALIDATION_ERROR]
    C -- válido --> D[chat.send_message]
    D --> E{conversation.doctor_id == user.id?}
    E -- não --> E1[403 FORBIDDEN]
    E -- sim --> F{messages.count >= MAX_MESSAGES?}
    F -- sim --> F1[400 CONVERSATION_FULL]
    F -- não --> G[is_first = count==0]
    G --> H[atomic: Message.create role USER]
    H --> I[orchestrator.generate user, conv, content, is_first]
    I --> J[assistant = Message.create role ASSISTANT, content, tokens_used, blocked, metadata citações]
    J --> K[conv.save updated_at]
    K --> L[201 MessageSerializer]
```

> `MAX_MESSAGES` aqui vem do env `MAX_MESSAGES_PER_CONVERSATION` (chat.py:7), default 50. `CONVERSATION_FULL` é o código real lançado (documentado como `CONVERSATION_LIMIT_REACHED`). 🟢

## 4. Stream SSE (GET `/api/v1/conversations/<id>/stream/?token=&prompt=`)

```mermaid
flowchart TD
    A[GET stream] --> B{token?}
    B -- não --> B1[401 SSE UNAUTHORIZED Token ausente]
    B -- sim --> C[AccessToken token_str + User.get id=token.user_id]
    C -- inválido/erro --> C1[401 SSE UNAUTHORIZED Token inválido]
    C -- válido --> D{conversa do médico?}
    D -- não --> D1[404 SSE NOT_FOUND]
    D -- sim --> E{prompt não vazio?}
    E -- não --> E1[400 SSE VALIDATION_ERROR Prompt vazio]
    E -- sim --> F{messages.count >= MAX_MESSAGES 50?}
    F -- sim --> F1[400 SSE CONVERSATION_FULL]
    F -- não --> G[is_first = count==0]
    G --> H[Message.create role USER]
    H --> I{título vazio ou Nova conversa?}
    I -- sim --> J[title = prompt[:80], save]
    I -- não --> K[generate_stream user, conv, prompt, is_first]
    J --> K
    K --> L{evento}
    L -- token --> L1[acumula full_content, yield data:event]
    L -- citation --> L2[acumula citações, yield data:event]
    L -- done --> L3[tokens_used, blocked, onboarding, missing_basics, data_capture, patient...]
    L -- error --> L4[logger.warning stream_error, yield data:event]
    L1 --> K
    L2 --> K
    L3 --> M[Message.create role ASSISTANT content=join, tokens_used, blocked, metadata]
    L4 --> K
    M --> N[conv.save updated_at]
    N --> O[yield data:done]
```

> View Django pura (sem `@api_view`): não passa pelo renderer/exception handler/throttle do DRF. Erros são emitidos como eventos SSE com status HTTP correspondente. Headers: `Cache-Control: no-cache` e `X-Accel-Buffering: no`. 🟢

## 5. Boas-vindas (`ensure_welcome_conversation`)

```mermaid
flowchart TD
    A[user] --> B{role == ADMIN?}
    B -- sim --> C[return None]
    B -- não --> D[all_objects filter doctor, title Bem-vindo]
    D -- existe --> E[return existing idempotente]
    D -- não --> F[Conversation.create doctor, title Bem-vindo]
    F --> G[Message.create role ASSISTANT, WELCOME_MESSAGE + DISCLAIMER, tokens_used 0, metadata welcome:true]
    G --> H[return conv]
```

> Mensagem estática, sem LLM. Chamado no cadastro (`accounts.views.register`). 🟢

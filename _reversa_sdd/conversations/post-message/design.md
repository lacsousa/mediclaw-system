# Conversations / Post Message, Design Técnico

> Contrato operacional de **COMO** o envio de mensagem é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| POST | `/api/v1/conversations/<id>/messages/` | `{content}` | `Message` (assistente) | 201, 400, 403, 404, 401 | `IsAuthenticated` + chat throttle |

## Fluxo Principal

1. `conv = Conversation.objects.get(pk=id, doctor=request.user)`; inexistente → 404. (`apps/conversations/views.py`) 🟢
2. `CreateMessageInput` valida `content` (1–4000); inválido → 400. (`serializers.py`) 🟢
3. `chat.send_message(...)`:
   - Revalida `conversation.doctor_id == user.id`; senão → 403 `FORBIDDEN`. (`services/chat.py`) 🟢
   - Checa `messages.count() >= MAX_MESSAGES` (env, default 50); senão → 400 `CONVERSATION_FULL`. (`chat.py:7`) 🟢
   - `is_first = count == 0`. (`chat.py`) 🟢
   - `transaction.atomic()`: cria `Message(role=USER)`; chama `orchestrator.generate(user, conv, content, is_first)`; cria `Message(role=ASSISTANT, content, tokens_used, blocked, metadata=citações)`; `conv.save(update_fields=["updated_at"])`. (`chat.py`) 🟢
4. Retorna `201 MessageSerializer`. (`views.py`) 🟢

## Fluxos Alternativos

- **[Conversa inexistente]:** 404 `NOT_FOUND`. 🟢
- **[Conteúdo inválido]:** 400 `VALIDATION_ERROR`. 🟢
- **[Limite atingido]:** 400 `CONVERSATION_FULL` (código real; o doc global lista `CONVERSATION_LIMIT_REACHED`). 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.ai_engine.orchestrator.generate` | Geração da resposta | chamada dentro da transação |
| `apps.conversations.models.Message` | Persistência | `Message.objects.create(role=..., ...)` |
| `apps.common.exceptions.AppError` | Erros de negócio | `FORBIDDEN`, `NOT_FOUND`, `CONVERSATION_FULL` |
| `config.settings.MAX_MESSAGES_PER_CONVERSATION` | Limite | `chat.py:7` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Limite de mensagens lido do env com default 50 | `chat.py:7` | 🟢 |
| Persistência atômica (USER + ASSISTANT juntas) | `chat.py` | 🟢 |
| `is_first` para onboarding do orquestrador | `chat.py` | 🟢 |
| Dupla checagem de ownership (404 na view, 403 no service) | `views.py`; `chat.py` | 🟢 |
| Throttle de chat dedicado (`chat: 10/min`) | `settings.py:127` | 🟢 |

## Riscos e Lacunas

- 🔴 Divergência de código de erro: `CONVERSATION_FULL` lançado vs `CONVERSATION_LIMIT_REACHED` documentado — alinhar.
- 🟡 `MAX_MESSAGES` lido do env no `chat.py` (não via settings padrão) — verificar leitura de env fora do `settings.py`.
- 🟡 Chamada ao LLM dentro da transação pode segurar lock no Postgres durante a geração — avaliar.

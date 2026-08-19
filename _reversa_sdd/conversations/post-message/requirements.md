# Conversations / Post Message — Requisitos

> Contrato operacional do caso de uso **Enviar mensagem** (`POST /api/v1/conversations/<id>/messages/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Envia uma mensagem do usuário para a conversa e dispara o orquestrador de IA para gerar a resposta do assistente (não-stream). Persiste ambas as mensagens de forma atômica, contabiliza tokens e bloqueio de guardrail, e atualiza o `updated_at` da conversa.

## Regras de Negócio

- **RN-01** — Rota protegida por `IsAuthenticated` e throttle de chat (`10/min`). 🟢
- **RN-02** — `content` validado com `1 ≤ len ≤ 4000`. 🟢
- **RN-03** — Conversa inexistente/fora do escopo → 404. 🟢
- **RN-04** — `conversation.doctor_id != user.id` → 403 `FORBIDDEN` (dupla checagem). 🟢
- **RN-05** — Limite: `messages.count() >= MAX_MESSAGES_PER_CONVERSATION` (default 50) → 400 `CONVERSATION_FULL`. 🟢
- **RN-06** — `is_first = count == 0` informa o orquestrador (onboarding). 🟢
- **RN-07** — Persistência atômica: mensagem USER + resposta ASSISTANT (`Message.create`) + `conv.save(updated_at)` em transação. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Enviar mensagem e obter resposta | Must | POST `/api/v1/conversations/<id>/messages/` `{content}` → 201 `MessageSerializer` (resposta) |
| RF-02 | Validar conteúdo | Must | `content` vazio/ausente ou > 4000 → 400 `VALIDATION_ERROR` |
| RF-03 | Aplicar limite de mensagens | Must | Conversa com ≥ 50 mensagens → 400 `CONVERSATION_FULL` |
| RF-04 | Bloquear dono incorreto | Must | `conversation.doctor_id != user.id` → 403 `FORBIDDEN` |

## Critérios de Aceitação

```gherkin
Dado uma conversa do médico com content válido
Quando faço POST em /api/v1/conversations/<id>/messages/
Então recebo 201 com a resposta do assistente e a conversa tem as duas novas mensagens

Dado um content vazio ou com mais de 4000 caracteres
Quando faço POST em /api/v1/conversations/<id>/messages/
Então recebo 400 VALIDATION_ERROR

Dado uma conversa com 50 mensagens
Quando faço POST em /api/v1/conversations/<id>/messages/
Então recebo 400 CONVERSATION_FULL

Dado um usuário autenticado que não é o dono da conversa
Quando faço POST em /api/v1/conversations/<id>/messages/
Então recebo 403 FORBIDDEN
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/conversations/views.py` | `post_message` | 🟢 |
| `apps/conversations/serializers.py` | `CreateMessageInput` | 🟢 |
| `apps/conversations/services/chat.py` | `send_message` | 🟢 |
| `apps/ai_engine/orchestrator.py` | `generate` | 🟢 |
| `config/settings.py:127` | throttle `chat: 10/min` | 🟢 |

# Conversations / Post Message, Tarefas de Implementação

> Sequência executável para reimplementar o envio de mensagem a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos `Conversation` e `Message`
- [ ] Orquestrador de IA com `generate` (ver ai_engine)
- [ ] Throttle `chat` configurado no settings

## Tarefas

- [ ] **T-01**, Serializer `CreateMessageInput` validando `content` 1–4000
  - Origem no legado: `apps/conversations/serializers.py`
  - Critério de pronto: `content` vazio/ausente ou > 4000 → 400 `VALIDATION_ERROR`
  - Confiança: 🟢

- [ ] **T-02**, Service `chat.send_message` com limite, atomicidade e orquestração
  - Origem no legado: `apps/conversations/services/chat.py`
  - Critério de pronto: revalida ownership (403); limite `MAX_MESSAGES_PER_CONVERSATION` → 400 `CONVERSATION_FULL`; `is_first`; `transaction.atomic` com USER + ASSISTANT + `updated_at`
  - Confiança: 🟢

- [ ] **T-03**, View `post_message` com 404 e throttle de chat
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: POST → 201; `IsAuthenticated` + throttle `chat`; 404 para conversa inexistente
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Envio happy path → 201 com resposta e 2 mensagens novas
- [ ] **TT-02**, Content vazio/ausente ou > 4000 → 400
- [ ] **TT-03**, Conversa com ≥ 50 mensagens → 400 `CONVERSATION_FULL`
- [ ] **TT-04**, Usuário não-dono → 403 `FORBIDDEN`
- [ ] **TT-05**, Throttle de chat (10/min) respeitado

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-05 (TT-02 depende do orquestrador/LLM — mockar chamada externa).

## Lacunas Pendentes (🔴)

- [ ] Alinhar código de erro (`CONVERSATION_FULL` vs `CONVERSATION_LIMIT_REACHED`).
- [ ] Verificar leitura de `MAX_MESSAGES_PER_CONVERSATION` fora do `settings.py` (viola convenção).
- [ ] Avaliar chamada ao LLM dentro de transação (lock no Postgres durante geração).

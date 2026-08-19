# Conversations / Welcome, Design Técnico

> Contrato operacional de **COMO** a conversa de boas-vindas é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `ensure_welcome_conversation` | `(user) -> Conversation \| None` | conversa "Bem-vindo" ou `None` (admin) |

> ⚠️ **Não é endpoint.** Não há rota `welcome/` no urlconf de conversations (`apps/conversations/urls.py`). É serviço chamado no cadastro (`accounts.views.register`). 🟢

## Fluxo Principal

1. `user.role == "ADMIN"` → `return None`. 🟢
2. `conv = Conversation.all_objects.filter(doctor=user, title="Bem-vindo")` → se existe, `return conv` (idempotente). 🟢
3. `conv = Conversation.objects.create(doctor=user, title="Bem-vindo")`. 🟢
4. `Message.objects.create(conversation=conv, role="ASSISTANT", content=WELCOME_MESSAGE + DISCLAIMER, tokens_used=0, metadata={"welcome": True})`. 🟢
5. `return conv`. 🟢

## Fluxos Alternativos

- **[Usuário ADMIN]:** retorna `None` — sem conversa de boas-vindas. 🟢
- **[Conversa já existente]:** retorna a existente (usa `all_objects`, cobrindo inclusive soft-deletadas). 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.conversations.models.Conversation` | Persistência | `all_objects.filter(...)` / `objects.create(...)` |
| `apps.conversations.models.Message` | Mensagem inicial | `Message.objects.create(role=ASSISTANT, ...)` |
| `apps.ai_engine.prompts` | Texto estático | `WELCOME_MESSAGE`, `DISCLAIMER` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Boas-vindas como conversa real (não só mensagem na resposta de cadastro) | `register`/serializer do cadastro dispara o serviço | 🟢 |
| Idempotência via `all_objects` + título fixo "Bem-vindo" | `welcome.py:27-29` | 🟢 |
| `WELCOME_MESSAGE` definida no próprio módulo, terminando com `DISCLAIMER` | `welcome.py:9-22` | 🟢 |
| Mensagem estática com `tokens_used=0`, `blocked_by_guardrail=False`, `metadata={"welcome": True}` | `welcome.py:38-44` | 🟢 |
| Sem LLM — nada é gerado | `welcome.py` (importa só `DISCLAIMER`) | 🟢 |

## Riscos e Lacunas

- 🟡 Título fixo "Bem-vindo" como chave de idempotência — usuário que renomear a conversa gera nova na próxima chamada.
- 🟡 `all_objects` inclui soft-deletadas — conversa deletada "Bem-vindo" pode ser ressuscitada na idempotência.
- 🟡 Ponto exato de disparo no cadastro (view `register` vs `RegisterSerializer.create`) a confirmar.

# Conversations / Welcome, Tarefas de Implementação

> Sequência executável para reimplementar a conversa de boas-vindas a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos `Conversation` (com `all_objects` para soft delete) e `Message`
- [ ] `DISCLAIMER` em `apps/ai_engine/prompts.py` (importado pelo serviço); `WELCOME_MESSAGE` é definida no próprio módulo

## Tarefas

- [ ] **T-01**, Serviço `ensure_welcome_conversation(user)` idempotente
  - Origem no legado: `apps/conversations/services/welcome.py:23`
  - Critério de pronto: ADMIN → `None`; existente → retorna; senão cria `Conversation("Bem-vindo")` + `Message(ASSISTANT, WELCOME_MESSAGE, tokens_used=0, blocked_by_guardrail=False, metadata={"welcome": True})`
  - Confiança: 🟢

- [ ] **T-02**, Chamada no cadastro (`register`)
  - Origem no legado: `apps/accounts/views.py`
  - Critério de pronto: após criar usuário, invoca o serviço; falha não impede o cadastro
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Cadastro não-admin → conversa "Bem-vindo" com mensagem inicial (WELCOME_MESSAGE + DISCLAIMER)
- [ ] **TT-02**, Chamada repetida → mesma conversa, sem duplicar
- [ ] **TT-03**, Cadastro ADMIN → `None`, sem conversa
- [ ] **TT-04**, Mensagem sem LLM: `tokens_used=0` e `metadata.welcome=True`

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 a TT-04.

## Lacunas Pendentes (🔴)

- [ ] Confirmar path exato do serviço no legado (`apps/conversations/services/...`).
- [ ] Avaliar idempotência quando a conversa "Bem-vindo" foi renomeada ou soft-deletada.

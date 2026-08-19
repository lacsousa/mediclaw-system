# Conversations / Welcome — Requisitos

> Contrato operacional do caso de uso **Conversa de boas-vindas** (`ensure_welcome_conversation`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Cria a conversa de boas-vindas **automaticamente no cadastro do usuário** (chamado em `accounts.views.register`). NÃO é um endpoint: é uma função de serviço idempotente que garante que todo usuário não-admin tenha uma conversa "Bem-vindo" com a mensagem inicial do assistente (`WELCOME_MESSAGE + DISCLAIMER`), sem chamada ao LLM.

## Regras de Negócio

- **RN-01** — `role == ADMIN` → retorna `None` (sem conversa de boas-vindas). 🟢
- **RN-02** — Idempotente: busca conversa existente (`all_objects`, título "Bem-vindo") e retorna se já existir. 🟢
- **RN-03** — Inexistente → cria `Conversation(doctor=user, title="Bem-vindo")` + `Message(role=ASSISTANT, content=WELCOME_MESSAGE + DISCLAIMER, tokens_used=0, metadata={"welcome": True})`. 🟢
- **RN-04** — Mensagem estática, **sem LLM**. 🟢
- **RN-05** — Disparado no cadastro (`register`), não exposto via rota. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Garantir boas-vindas no cadastro | Must | Ao registrar usuário não-admin, existe conversa "Bem-vindo" com mensagem inicial |
| RF-02 | Ser idempotente | Must | Chamadas repetidas retornam a mesma conversa (sem duplicar) |
| RF-03 | Ignorar admin | Must | Cadastro de ADMIN → `None`, sem conversa |
| RF-04 | Não chamar LLM | Must | Mensagem é `WELCOME_MESSAGE + DISCLAIMER`, `tokens_used=0` |

## Critérios de Aceitação

```gherkin
Dado o registro de um usuário não-admin
Quando chamo ensure_welcome_conversation
Então é criada a conversa "Bem-vindo" com a mensagem inicial (WELCOME_MESSAGE + DISCLAIMER)

Dado que a conversa "Bem-vindo" já existe
Quando chamo ensure_welcome_conversation de novo
Então retorna a conversa existente, sem duplicar

Dado o registro de um usuário ADMIN
Quando chamo ensure_welcome_conversation
Então retorna None
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/conversations/services/welcome.py:23` | `ensure_welcome_conversation` | 🟢 |
| `apps/conversations/services/welcome.py:6-14` | `WELCOME_CONVERSATION_TITLE`, `WELCOME_METADATA_FLAG`, `WELCOME_MESSAGE` | 🟢 |
| `apps/accounts/views.py` | `register` (fluxo de cadastro dispara o serviço) | 🟢 |
| `apps/ai_engine/prompts.py` | `DISCLAIMER` (concatenado ao final de `WELCOME_MESSAGE`) | 🟢 |
| `apps/conversations/models.py` | `Conversation`, `Message` | 🟢 |

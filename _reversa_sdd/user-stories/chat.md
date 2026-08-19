# User Stories — Chat e Conversas

> Fluxo: conversas, envio de mensagem, streaming SSE e boas-vindas.
> Cobertura: módulo `conversations`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-CHAT-01 — Listar e criar conversas

**Como** médico,
**quero** listar minhas conversas e abrir novas,
**para** organizar atendimentos por paciente/tema.

- Critérios de aceite:
  - GET `/api/v1/conversations/` → 200 lista.
  - POST `/api/v1/conversations/` (body ignorado) → 201 conversa com `title="Nova conversa"`; o título pode ser substituído pelos primeiros 80 chars do primeiro prompt. 🟢 [Revisão Codex]
  - Escopo ao médico logado. 🟢

## US-CHAT-02 — Ver detalhe e excluir conversa

**Como** médico,
**quero** ver as mensagens de uma conversa e excluí-la,
**para** revisar o histórico e remover conversas encerradas.

- Critérios de aceite:
  - GET `/api/v1/conversations/<id>/` → 200 conversa + mensagens.
  - DELETE → 204 **soft delete** (`deleted_at`; some da listagem, permanece em `all_objects`).
  - Conversa inexistente/outro dono → 404. 🟢

## US-CHAT-03 — Enviar mensagem e receber resposta

**Como** médico,
**quero** enviar uma mensagem e receber a resposta do assistente,
**para** obter apoio educacional para o atendimento.

- Critérios de aceite:
  - POST `/api/v1/conversations/<id>/messages/` `{content}` → 201 resposta (persistida).
  - Content vazio ou > 4000 → 400 `VALIDATION_ERROR`.
  - Conversa com ≥ 50 mensagens → 400 `CONVERSATION_FULL`.
  - Usuário não-dono → 403 `FORBIDDEN`.
  - Throttle de chat (10/min) → 429. 🟢

## US-CHAT-04 — Receber resposta em streaming (SSE)

**Como** médico,
**quero** ver a resposta da IA aparecendo token a token,
**para** sentir a resposta imediata e interromper se necessário.

- Critérios de aceite:
  - GET `/api/v1/conversations/<id>/stream/?token=<access>` → `text/event-stream`.
  - Eventos: `citation` (chunks RAG) → `token*` → `done` (ou `error`).
  - Erro do LLM → evento `error` com `code: LLM_PROVIDER_ERROR`. 🟢

## US-CHAT-05 — Resposta segura com disclaimer

**Como** plataforma,
**quero** que toda resposta educacional venha acompanhada do disclaimer,
**para** deixar claro que a IA não substitui o médico (LGPD / restrição crítica).

- Critérios de aceite:
  - Guardrail de entrada/saída bloqueia diagnóstico, prescrição e urgência → resposta canônica + DISCLAIMER.
  - REST anexa o DISCLAIMER ao final se ausente. 🟢 (🔴 streaming não anexa — lacuna)

## US-CHAT-06 — Conversa de boas-vindas automática

**Como** médico recém-cadastrado,
**quero** encontrar uma conversa "Bem-vindo" pronta,
**para** entender como usar o MediClaw sem precisar criar nada.

- Critérios de aceite:
  - `ensure_welcome_conversation(user)` chamado no cadastro → cria `Conversation("Bem-vindo")` + `Message` estática (`WELCOME_MESSAGE`, sem LLM).
  - Idempotente (não duplica); ADMIN → `None`. 🟢

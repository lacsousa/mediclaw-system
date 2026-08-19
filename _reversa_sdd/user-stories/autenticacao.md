# User Stories — Autenticação

> Fluxo: cadastro, login, refresh, perfil e criação de usuários admin.
> Cobertura: módulos `accounts` (+ auditoria `ADMIN_CREATED_USER`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-AUTH-01 — Cadastro com consentimento LGPD

**Como** médico interessado na plataforma,
**quero** me cadastrar com e-mail, senha, nome e aceite dos termos,
**para** acessar o MediClaw e começar a usar a IA preventiva.

- Critérios de aceite:
  - POST `/api/v1/auth/register/` com `{email, password, name, accept_terms}` → 201 `{access, refresh, user}`.
  - `accept_terms` falso → 400 `VALIDATION_ERROR` ("Aceite dos termos é obrigatório.").
  - `password` sem ≥8 chars com letra e dígito → 400.
  - E-mail duplicado → 400 `EMAIL_ALREADY_EXISTS`.
  - Usuário recebe automaticamente a conversa "Bem-vindo" (ver US-CHAT-06). 🟢

## US-AUTH-02 — Login com JWT

**Como** usuário cadastrado,
**quero** fazer login com e-mail e senha,
**para** obter um access token (30 min) e refresh token (1 dia).

- Critérios de aceite:
  - POST `/api/v1/auth/login/` → 200 `{access, refresh, user}`.
  - Credenciais inválidas → 400 `INVALID_CREDENTIALS`.
  - Access expirado → refresh via POST `/api/v1/auth/refresh/` devolve novo access. 🟢

## US-AUTH-03 — Ver e atualizar perfil

**Como** usuário autenticado,
**quero** consultar e complementar meu perfil (primeiro nome),
**para** personalizar minha experiência.

- Critérios de aceite:
  - GET `/api/v1/auth/me/` → 200 `User` sempre (inclusive com `first_name` vazio — não há 204). 🟢 [Revisão Codex]
  - PATCH `/api/v1/auth/me/` `{name?/email?}` → 200 com perfil atualizado (parcial). 🟢 [Revisão Codex]
  - DELETE `/api/v1/auth/me/` → 204 com remoção em cascata (LGPD). 🟢 [Revisão Codex]
  - Persistir nome (persist_user_name) → `{first_name}` refletido no perfil. 🟢

## US-AUTH-04 — Admin cria usuários

**Como** administrador,
**quero** criar usuários diretamente,
**para** provisionar contas sem depender do cadastro público.

- Critérios de aceite:
  - POST `/api/v1/admin/users/` → 201 `User`.
  - Acesso restrito a role `ADMIN` → 403 `FORBIDDEN`.
  - Registra evento `ADMIN_CREATED_USER` (auditoria — stub no MVP). 🟢

## US-AUTH-05 — Segurança e LGPD

**Como** plataforma,
**quero** nunca logar PII (e-mail, mensagens, dados biométricos),
**para** cumprir a LGPD (Art. 11 — dados de saúde sensíveis).

- Critérios de aceite:
  - Nenhum `print`/log contém e-mail, conteúdo de mensagens ou dados de saúde.
  - `accepted_terms_at` persistido no cadastro (consentimento explícito). 🟢

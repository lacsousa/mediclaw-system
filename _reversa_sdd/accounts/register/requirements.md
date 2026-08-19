# Accounts / Register — Requisitos

> Contrato operacional do caso de uso **Cadastro de usuário** (`POST /api/v1/auth/register/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Cria um usuário do MediClaw com e-mail, senha e consentimento LGPD explícito; emite access + refresh JWT; dispara a criação da conversa de boas-vindas para usuários não-ADMIN; audita o evento `USER_REGISTERED` (stub no legado).

## Regras de Negócio

- **RN-01** — E-mail normalizado para minúsculas e único (`iexact`). 🟢
- **RN-02** — Senha ≥ 8 caracteres com pelo menos uma letra e um dígito (`PASSWORD_RX`). 🟢
- **RN-03** — `accept_terms` obrigatório; `accepted_terms_at=timezone.now()` gravado no cadastro. 🟢
- **RN-04** — Conversa de boas-vindas criada via `ensure_welcome_conversation`, idempotente, pulada para role `ADMIN`. 🟢
- **RN-05** — Senha nunca armazenada em texto puro (`set_password`). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Cadastro com e-mail, senha, nome e `accept_terms` retornando access + refresh + user | Must | POST `/api/v1/auth/register/` payload válido → 201 `{access, refresh, user}` com `accepted_terms_at` preenchido |
| RF-02 | Validação de senha forte | Must | Senha sem letra/dígito ou < 8 chars → 400 `VALIDATION_ERROR` |
| RF-03 | Validação de e-mail único | Must | E-mail já cadastrado (qualquer caixa) → 400 `VALIDATION_ERROR` |
| RF-04 | Obrigatoriedade do consentimento LGPD | Must | `accept_terms` ausente/falso → 400 `VALIDATION_ERROR` |
| RF-05 | Criação da conversa de boas-vindas pós-cadastro | Should | Usuário não-ADMIN recebe conversa "Bem-vindo" com mensagem + disclaimer; ADMIN não recebe |

## Critérios de Aceitação

```gherkin
Dado um e-mail válido, senha com ≥ 8 chars (letra + dígito) e accept_terms=true
Quando faço POST em /api/v1/auth/register/
Então recebo 201 com access, refresh e user (accepted_terms_at preenchido)
E uma conversa de boas-vindas é criada para o usuário

Dado uma senha sem dígito ou accept_terms ausente
Quando faço POST em /api/v1/auth/register/
Então recebo 400 VALIDATION_ERROR com detalhes do campo inválido

Dado um e-mail já cadastrado (em qualquer caixa)
Quando faço POST em /api/v1/auth/register/ com o mesmo e-mail
Então recebo 400 VALIDATION_ERROR indicando e-mail já em uso
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/accounts/serializers.py:6-42` | `RegisterSerializer` (validação + create) | 🟢 |
| `apps/accounts/views.py:19-34` | `register` | 🟢 |
| `apps/accounts/models.py:5-19` | `UserManager.create_user` | 🟢 |
| `apps/conversations/services/welcome.py:23-50` | `ensure_welcome_conversation` | 🟢 |
| `apps/audit/services/log.py:1-4` | `record("USER_REGISTERED")` (stub) | 🟢 |
| `apps/accounts/urls.py` | rota `/auth/register/` | 🟢 |

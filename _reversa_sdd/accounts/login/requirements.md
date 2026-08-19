# Accounts / Login — Requisitos

> Contrato operacional do caso de uso **Login** (`POST /api/v1/auth/login/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Autentica usuário por e-mail + senha, emitindo access + refresh JWT. Falha de credencial, usuário inexistente e usuário inativo retornam **o mesmo** erro `INVALID_CREDENTIALS` (anti-enumeração — não vaza qual campo está errado). Audita `LOGIN` (stub).

## Regras de Negócio

- **RN-01** — E-mail normalizado para minúsculas antes da autenticação. 🟢
- **RN-02** — Usuário inexistente, senha errada ou `is_active` falso → `AppError("INVALID_CREDENTIALS", ..., 401)` idêntico em todos os casos. 🟢
- **RN-03** — Sucesso emite access + refresh via `RefreshToken.for_user`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Login com e-mail e senha retornando access + refresh + user | Must | POST `/api/v1/auth/login/` credenciais corretas → 200 `{access, refresh, user}` |
| RF-02 | Falha uniforme de credenciais | Must | Credenciais incorretas, usuário inexistente ou inativo → 401 `INVALID_CREDENTIALS` (mesmo corpo) |

## Critérios de Aceitação

```gherkin
Dado um e-mail/senha corretos de um usuário ativo
Quando faço POST em /api/v1/auth/login/
Então recebo 200 com access, refresh e user

Dado um e-mail/senha incorretos ou usuário inativo
Quando faço POST em /api/v1/auth/login/
Então recebo 401 INVALID_CREDENTIALS (mesmo erro nos três casos)
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/accounts/views.py:37-53` | `login` | 🟢 |
| `apps/accounts/serializers.py:44-52` | `LoginSerializer` | 🟢 |
| `django.contrib.auth` | `authenticate` | 🟢 |
| `apps/audit/services/log.py:1-4` | `record("LOGIN")` (stub) | 🟢 |

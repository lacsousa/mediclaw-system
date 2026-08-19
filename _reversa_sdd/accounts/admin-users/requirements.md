# Accounts / Admin Cria Usuário — Requisitos

> Contrato operacional do caso de uso **Criação de usuário por admin** (`POST /api/v1/admin/users/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Permite que um usuário com role `ADMIN` crie outro usuário (role `USER` ou `ADMIN`) com e-mail, senha e nome. A rota fica sob `/api/v1/admin/` e é protegida pela permission custom `IsAdminRole`. Usuários criados com role `USER` recebem a conversa de boas-vindas.

## Regras de Negócio

- **RN-01** — Apenas usuários com `role == "ADMIN"` autenticados podem criar usuários. 🟢
- **RN-02** — `role` informada deve pertencer a `{USER, ADMIN}`; default `USER`. 🟢
- **RN-03** — Senha validada com `PASSWORD_RX` (≥ 8 chars, letra + dígito) e e-mail único (`iexact`). 🟢
- **RN-04** — Usuário criado com role `USER` recebe conversa de boas-vindas idempotente; role `ADMIN` não. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Criar usuário com role definida | Must | POST `/api/v1/admin/users/` com role ADMIN → 201 `UserSerializer` |
| RF-02 | Bloquear não-ADMIN | Must | Usuário role USER → 403 `FORBIDDEN` |
| RF-03 | Validar payload (senha, e-mail único, role válida) | Must | Payload inválido → 400 `VALIDATION_ERROR` |
| RF-04 | Disparar conversa de boas-vindas para role USER | Should | Usuário criado com role USER recebe conversa "Bem-vindo" |

## Critérios de Aceitação

```gherkin
Dado um usuário autenticado com role ADMIN
Quando faço POST em /api/v1/admin/users/ com {email, password, name, role}
Então recebo 201 com o UserSerializer do usuário criado

Dado um usuário autenticado com role USER
Quando faço POST em /api/v1/admin/users/
Então recebo 403 FORBIDDEN

Dado um payload com senha fraca, e-mail duplicado ou role inválida
Quando faço POST em /api/v1/admin/users/
Então recebo 400 VALIDATION_ERROR
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/accounts/views.py:56-63` | `admin_create_user` | 🟢 |
| `apps/accounts/serializers.py:63-91` | `AdminCreateUserSerializer` | 🟢 |
| `apps/common/permissions.py:4-10` | `IsAdminRole` | 🟢 |
| `apps/audit/urls.py` | rota `/admin/users/` | 🟢 |
| `apps/conversations/services/welcome.py` | `ensure_welcome_conversation` | 🟢 |

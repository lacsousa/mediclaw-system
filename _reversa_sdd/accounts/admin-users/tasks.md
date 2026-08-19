# Accounts / Admin Cria Usuário, Tarefas de Implementação

> Sequência executável para reimplementar a criação admin a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Permission `IsAdminRole` implementada (ver `common/tasks.md` T-07)
- [ ] Modelo `User` com campo `role`

## Tarefas

- [ ] **T-01**, `AdminCreateUserSerializer` validando senha, e-mail único e role
  - Origem no legado: `apps/accounts/serializers.py:63-91`
  - Critério de pronto: senha fraca → erro; e-mail duplicado → erro; `role` fora de `{USER, ADMIN}` → erro; `create` dispara conversa de boas-vindas para role USER
  - Confiança: 🟢

- [ ] **T-02**, View `admin_create_user` protegida por `IsAdminRole`
  - Origem no legado: `apps/accounts/views.py:56-63`
  - Critério de pronto: POST `/api/v1/admin/users/` exige role ADMIN; sucesso → 201 `UserSerializer` + `record("ADMIN_CREATED_USER")`
  - Confiança: 🟢

- [ ] **T-03**, Rota montada sob `/api/v1/admin/`
  - Origem no legado: `apps/audit/urls.py`; `config/urls.py:36`
  - Critério de pronto: rota acessível em `/api/v1/admin/users/`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, POST com role ADMIN → 201 `UserSerializer`
- [ ] **TT-02**, POST com role USER → 403 `FORBIDDEN`
- [ ] **TT-03**, POST com payload inválido (senha fraca, e-mail duplicado, role inválida) → 400 `VALIDATION_ERROR`
- [ ] **TT-04**, Usuário criado com role USER ganha conversa de boas-vindas; role ADMIN não

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-04.

## Lacunas Pendentes (🔴)

- [ ] Persistência real do evento `ADMIN_CREATED_USER` (audit stub).
- [ ] Decidir se a rota admin permanece em `apps/audit/urls.py` ou move para `accounts/urls.py`.

# Accounts / Admin Cria Usuário, Design Técnico

> Contrato operacional de **COMO** a criação admin é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| POST | `/api/v1/admin/users/` | `{email, password, name, role}` | `User` | 201, 400, 403 | `IsAdminRole` |

## Fluxo Principal

1. `IsAdminRole.has_permission` exige `request.user.is_authenticated` e `request.user.role == "ADMIN"`. (`apps/common/permissions.py:4-10`) 🟢
2. `AdminCreateUserSerializer` valida senha (`PASSWORD_RX`), e-mail único (`email__iexact`) e `role ∈ {USER, ADMIN}`. (`apps/accounts/serializers.py:63-79`) 🟢
3. `create_user(...)` cria o usuário com a `role` definida (default `USER`). (`serializers.py:81-86`) 🟢
4. `record("ADMIN_CREATED_USER", user=user)` (stub). (`views.py:60`) 🟢
5. Se role == `USER`, `ensure_welcome_conversation(user)` cria a conversa de boas-vindas. (`serializers.py:88-90`) 🟢
6. Retorna `201 UserSerializer`. 🟢

## Fluxos Alternativos

- **[Não-ADMIN]:** 403 `FORBIDDEN` (permission `IsAdminRole`). (`permissions.py:4-10`) 🟢
- **[Role inválida]:** `ValidationError` em `role` (fora de `{USER, ADMIN}`) → 400. (`serializers.py:74-78`) 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.common.permissions.IsAdminRole` | Gate administrativo | `permission_classes = [IsAdminRole]` |
| `apps.conversations.services.welcome` | Onboarding | `ensure_welcome_conversation` |
| `apps.audit.services.log.record` | Auditoria | `ADMIN_CREATED_USER` — stub |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Gate por role (`IsAdminRole`) em vez de `is_staff`/`is_superuser` | `permissions.py:4-10` | 🟢 |
| Validação de senha duplicada com o `RegisterSerializer` | `serializers.py:6,16,70` | 🟢 |
| Rota montada em `apps/audit/urls.py` (não em accounts) | `audit/urls.py` | 🟢 |

## Riscos e Lacunas

- 🟡 A rota fica em `apps/audit/urls.py`, não em `accounts/urls.py` — acoplamento de roteamento a considerar na reimplementação.
- 🔴 `record()` do audit não persiste o evento.
- 🟡 `create_superuser` (seed) não valida `PASSWORD_RX` — divergência de política entre seed e serializer.

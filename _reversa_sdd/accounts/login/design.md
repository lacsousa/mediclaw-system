# Accounts / Login, Design Técnico

> Contrato operacional de **COMO** o login é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| POST | `/api/v1/auth/login/` | `{email, password}` | `{access, refresh, user}` | 200, 401 | `AllowAny` |

## Fluxo Principal

1. `email = request.data["email"].lower()` — normalização para minúsculas. (`apps/accounts/views.py:40`) 🟢
2. `authenticate(username=email, password=password)` valida credenciais. (`apps/accounts/views.py:42`) 🟢
3. Se `authenticate` retorna `None` (usuário inexistente ou senha errada) **ou** `not user.is_active` → `AppError("INVALID_CREDENTIALS", ..., 401)` — mesmo erro. (`apps/accounts/views.py:43-44`) 🟢
4. `RefreshToken.for_user(user)` gera access + refresh. (`apps/accounts/views.py:46`) 🟢
5. `record("LOGIN", user=user)` (stub) e retorna `200 {access, refresh, user}`. (`apps/accounts/views.py:48-51`) 🟢

## Fluxos Alternativos

- **[Credenciais inválidas]:** 401 `INVALID_CREDENTIALS` idêntico para usuário inexistente, senha errada ou inativo. (`views.py:43-44`) 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `django.contrib.auth.authenticate` | Validação de credenciais | `authenticate(username=email, password=password)` |
| `rest_framework_simplejwt` | Emissão de tokens | `RefreshToken.for_user` |
| `apps.common.exceptions.AppError` | Erro uniforme de login | `INVALID_CREDENTIALS` 401 |
| `apps.audit.services.log.record` | Auditoria | `LOGIN` — stub |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Anti-enumeração: mesmo erro para inexistente/senha errada/inativo | `views.py:43-44` | 🟢 |
| Normalização de e-mail para minúsculas no login | `views.py:40` | 🟢 |
| Auditoria `LOGIN` chamada, mas stub (ADR-007) | `audit/services/log.py` | 🟢 |

## Riscos e Lacunas

- 🔴 `record()` do audit não persiste — sem trilha real de logins.
- 🟡 Sem throttling específico na rota `login` — força bruta mitigada apenas pelo throttle global anon (30/min).

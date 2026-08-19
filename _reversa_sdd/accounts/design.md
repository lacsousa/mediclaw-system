# Accounts, Design Técnico

> Contrato operacional de **COMO** a unit `accounts` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

### Endpoints HTTP

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| POST | `/api/v1/auth/register/` | `{email, password, name, accept_terms}` | `{access, refresh, user}` | 201, 400 | `AllowAny` |
| POST | `/api/v1/auth/login/` | `{email, password}` | `{access, refresh, user}` | 200, 401 | `AllowAny` |
| POST | `/api/v1/auth/refresh/` | `{refresh}` | `{access}` | 200, 401 | `AllowAny` |
| GET | `/api/v1/auth/me/` | — | `User` | 200, 401 | `IsAuthenticated` |
| PATCH | `/api/v1/auth/me/` | `{name?, email?}` | `User` | 200, 400, 401 | `IsAuthenticated` |
| DELETE | `/api/v1/auth/me/` | — | `204 No Content` | 204, 401 | `IsAuthenticated` |
| POST | `/api/v1/admin/users/` | `{email, password, name, role}` | `User` | 201, 400, 403 | `IsAdminRole` |

**Formato de `User`** (via `UserSerializer`): `{id, email, first_name, role, accepted_terms_at}`. 🟢
**Payload de erro** (via `envelope_exception_handler`): `{data: null, error: {code, message, details}, meta: {}}`. 🟢

### Funções / classes

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `UserManager.create_user` | `(email: str, password: str \| None, **extra) -> User` | `User` | Normaliza e-mail, aplica `set_password` (hash) |
| `UserManager.create_superuser` | `(email: str, password: str \| None, **extra) -> User` | `User` | Força `is_staff`, `is_superuser`, `role=ADMIN` |
| `persist_user_name` | `(user_id: int, name: str) -> dict` | `{"first_name": cleaned}` | Sem request HTTP; usado na captura via chat |
| `RegisterSerializer.create` | `(validated: dict) -> User` | `User` | Cria usuário + dispara conversa de boas-vindas |
| `RefreshToken.for_user` | `(user: User) -> RefreshToken` | `RefreshToken` | Emite access + refresh com claims padrão |

## Fluxo Principal

### 1. Cadastro (`POST /api/v1/auth/register/`)

1. `RegisterSerializer` valida: e-mail único (`iexact`), senha via `PASSWORD_RX`, `accept_terms` obrigatório. (`apps/accounts/serializers.py:9-42`) 🟢
2. `User.objects.create_user` cria o usuário com `first_name=name` e `accepted_terms_at=timezone.now()`. (`apps/accounts/serializers.py:32-38`) 🟢
3. `RefreshToken.for_user(user)` gera access + refresh. (`apps/accounts/views.py:25`) 🟢
4. `record("USER_REGISTERED", user=user)` é chamado — mas o serviço é stub (não persiste). (`apps/audit/services/log.py:1-4`) 🟢
5. `ensure_welcome_conversation(user)` cria a conversa de boas-vindas (idempotente, pulada para ADMIN). (`apps/conversations/services/welcome.py:23-50`) 🟢
6. Retorna `201 {access, refresh, user}`. 🟢

### 2. Login (`POST /api/v1/auth/login/`)

1. E-mail normalizado para minúsculas. (`apps/accounts/views.py:40`) 🟢
2. `authenticate(username=email, password=password)` valida credenciais. (`apps/accounts/views.py:42`) 🟢
3. Se usuário inexistente, senha errada **ou** `is_active` falso → `AppError("INVALID_CREDENTIALS", ..., 401)` — mesmo erro em todos os casos (anti-enumeração). (`apps/accounts/views.py:43-44`) 🟢
4. `record("LOGIN", user=user)` (stub) e retorna `200 {access, refresh, user}`. 🟢

### 3. Refresh (`POST /api/v1/auth/refresh/`)

- `TokenRefreshView` padrão do `simplejwt`; valida o refresh token e emite novo access. (`apps/accounts/urls.py:3,7`) 🟢
- O access token expirado retorna `TOKEN_EXPIRED` no cliente, que deve chamar esta rota. 🟡

### 4. Perfil próprio (`GET/PATCH/DELETE /api/v1/auth/me/`)

- **GET:** serializa `request.user` → `200 User`. (`apps/accounts/views.py:71-72`) 🟢
- **PATCH:** `MeUpdateSerializer` valida apenas campos enviados (`partial=True`); e-mail duplicado exceto o próprio usuário → erro; grava `update_fields=["first_name"]` e/ou `["email"]`. (`apps/accounts/views.py:74-89`) 🟢
- **DELETE:** `user.delete()` → `204`; remoção em cascata dos dependentes via `on_delete=CASCADE`. (`apps/accounts/views.py:91-93`) 🟢

### 5. Criação de usuário por admin (`POST /api/v1/admin/users/`)

1. `IsAdminRole` exige `role == "ADMIN"` no token autenticado. (`apps/common/permissions.py:4-10`) 🟢
2. `AdminCreateUserSerializer` valida senha, e-mail único e `role ∈ {USER, ADMIN}`. (`apps/accounts/serializers.py:63-79`) 🟢
3. Cria usuário com `role` definida e dispara conversa de boas-vindas. (`apps/accounts/serializers.py:81-91`) 🟢

### 6. Captura de nome via chat (`persist_user_name`)

1. `(name or "").strip()`; valida `2 ≤ len ≤ 120` — falha lança `ValidationError` do DRF. (`apps/accounts/services/persist.py:9-14`) 🟢
2. Busca usuário por `pk`, grava `first_name` com `update_fields`, retorna `{"first_name": cleaned}`. (`apps/accounts/services/persist.py:15-18`) 🟢

## Fluxos Alternativos

- **[E-mail já cadastrado]:** `validate_email` rejeita com "E-mail já cadastrado." no cadastro e no PATCH `/me` (neste último, excluindo o próprio `pk`). (`apps/accounts/serializers.py:27-30,55-60`) 🟢
- **[Senha fraca]:** senha sem ≥ 8 chars (com letra e dígito) → `ValidationError` "Senha deve ter ≥ 8 chars, com letra e dígito." — regra duplicada em `RegisterSerializer` e `AdminCreateUserSerializer`. 🟢
- **[`accept_terms` ausente/falso]:** cadastro rejeitado com "Aceite dos termos é obrigatório." (`apps/accounts/serializers.py:22-25`) 🟢
- **[Usuário ADMIN cadastrando]:** `ensure_welcome_conversation` retorna `None` — nenhuma conversa criada. (`apps/conversations/services/welcome.py:29-31`) 🟢
- **[Credenciais inválidas]:** 401 `INVALID_CREDENTIALS`, idêntico para usuário inexistente, senha errada ou inativo. (`apps/accounts/views.py:43-44`) 🟢
- **[Sem token]:** rotas `IsAuthenticated`/`IsAdminRole` → 401 (token ausente/inválido via simplejwt). 🟡

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `rest_framework_simplejwt` | Emissão e refresh de tokens | `RefreshToken.for_user` e `TokenRefreshView` (`views.py:25,45`; `urls.py:3`) |
| `apps.common.permissions.IsAdminRole` | Gate administrativo | Rota `/admin/users/` exige `role=ADMIN` |
| `apps.common.exceptions.AppError` | Erros de negócio com envelope | `INVALID_CREDENTIALS` 401 no login |
| `apps.audit.services.log.record` | Auditoria de eventos | `USER_REGISTERED`, `LOGIN`, `ADMIN_CREATED_USER` — **stub, não persiste** |
| `apps.conversations.services.welcome.ensure_welcome_conversation` | Onboarding pós-cadastro | Cria conversa de boas-vindas idempotente |
| `django.contrib.auth` | `authenticate`, `AbstractUser`, `BaseUserManager` | Login e modelo de usuário |
| `config.settings.SIMPLE_JWT` | Configuração de lifetime dos tokens | `ACCESS_TOKEN_MINUTES=30`, `REFRESH_TOKEN_DAYS=1` |
| `config/urls.py` | Montagem das rotas | `api/v1/auth/` e `api/v1/admin/` |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Usuário custom identificado por e-mail (`USERNAME_FIELD="email"`, `username` em branco) | `apps/accounts/models.py:24-30` | 🟢 |
| Hash de senha via `set_password` no manager | `apps/accounts/models.py:11` | 🟢 |
| Anti-enumeração: mesmo erro para usuário inexistente/senha errada/inativo | `apps/accounts/views.py:43-44` | 🟢 |
| Normalização de e-mail para minúsculas no login e no cadastro | `apps/accounts/views.py:40`; `serializers.py:30` | 🟢 |
| Unicidade case-insensitive via `email__iexact` | `apps/accounts/serializers.py:28,58` | 🟢 |
| Consentimento LGPD como campo de auditoria (`accepted_terms_at`) preenchido no cadastro | `apps/accounts/serializers.py:37` | 🟢 |
| Conversa de boas-vindas idempotente, pulada para ADMIN | `apps/conversations/services/welcome.py:29-41` | 🟢 |
| Deleção em cascata de dados sensíveis (LGPD Art. 11) | `apps/accounts/views.py:92`; `apps/patients/models.py:11` | 🟢 |
| Auditoria por evento (`record(...)`) com stub — adiada para Epic 3 | `apps/audit/services/log.py:1-4`; ADR-007 | 🟢 |
| Validação de senha por regex duplicada entre serializers (sem util compartilhado) | `apps/accounts/serializers.py:6,16,70` | 🟢 |
| Refresh usa `TokenRefreshView` padrão, sem customização | `apps/accounts/urls.py:3` | 🟢 |
| Rotas via function-based views com `@api_view` + `@permission_classes` (não ViewSets) | `apps/accounts/views.py:19-93` | 🟢 |

## Estado Interno

Modelo `User` (tabela herdada de `AbstractUser`, customizada):

| Campo | Tipo | Observação |
|-------|------|------------|
| `id` | PK auto | — |
| `email` | `EmailField(unique=True)` | Identificador de login; normalizado minúsculo |
| `first_name` | `CharField` | Nome exibido; alvo de `persist_user_name` e PATCH `/me` |
| `role` | `CharField(choices=[USER, ADMIN])` | Default `USER`; gate da rota admin |
| `accepted_terms_at` | `DateTimeField(null=True)` | Consentimento LGPD; preenchido no cadastro |
| campos herdados | `password`, `is_active`, `is_staff`, `is_superuser`, timestamps | De `AbstractUser` |

Campos removidos do significado padrão: `username` existe no schema mas fica em branco (`blank=True`). 🟢

## Observabilidade

- Eventos de auditoria chamam `apps.audit.services.log.record("USER_REGISTERED"|"LOGIN"|"ADMIN_CREATED_USER", ...)`. 🔴
- **Lacuna:** `record()` é `pass` — nenhum evento é de fato persistido nem logado. Nenhum log estruturado existe na unit. 🔴
- Nenhuma métrica de latência/falha de autenticação é emitida. 🔴

## Riscos e Lacunas

- 🔴 `record()` do audit não persiste eventos de auditoria — sem trilha de auditoria real para cadastro/login (ADR-007 adia para Epic 3).
- 🔴 Nenhum log de eventos de autenticação (`logging`) — falhas de login e registros não são observáveis em produção.
- 🟡 `authenticate()` usa `User.USERNAME_FIELD="email"`; o backend padrão consulta `email__iexact` apenas se o backend de auth estiver configurado — validar se `AUTHENTICATION_BACKENDS`/`AUTH_USER_MODEL` estão corretos no settings (não confirmado nesta leitura).
- 🟡 Validação de senha duplicada em dois serializers — risco de divergência futura.
- 🟡 Sem throttling explícito nas rotas `register`/`login` — suscetível a força bruta (checklist de segurança do projeto prevê throttling anon+user).
- 🔴 A criação de admin via `create_superuser` não valida `PASSWORD_RX` (usa `create_user` direto) — divergência de política de senha entre seed e serializers.

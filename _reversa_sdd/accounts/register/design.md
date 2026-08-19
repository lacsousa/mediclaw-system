# Accounts / Register, Design Técnico

> Contrato operacional de **COMO** o cadastro é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| POST | `/api/v1/auth/register/` | `{email, password, name, accept_terms}` | `{access, refresh, user}` | 201, 400 | `AllowAny` |

**Formato de `user`** (`UserSerializer`): `{id, email, first_name, role, accepted_terms_at}`. 🟢

## Fluxo Principal

1. `RegisterSerializer` valida: `PASSWORD_RX` (≥ 8 chars, letra + dígito), e-mail único via `email__iexact`, `accept_terms` obrigatório. (`apps/accounts/serializers.py:9-27`) 🟢
2. `User.objects.create_user(email=..., password=..., first_name=name)` cria o usuário; `accepted_terms_at=timezone.now()` setado no `create`. (`apps/accounts/serializers.py:32-38`; `models.py:6-13`) 🟢
3. `RefreshToken.for_user(user)` gera access + refresh JWT. (`apps/accounts/views.py:25`) 🟢
4. `record("USER_REGISTERED", user=user)` — serviço stub (`pass`). (`apps/audit/services/log.py:1-4`) 🟢
5. `ensure_welcome_conversation(user)` cria a conversa de boas-vindas (idempotente). (`apps/conversations/services/welcome.py:23-50`) 🟢
6. Retorna `201 {access, refresh, user}`. 🟢

## Fluxos Alternativos

- **[Senha fraca]:** `ValidationError` "Senha deve ter ≥ 8 chars, com letra e dígito." → 400. (`serializers.py:16-19`) 🟢
- **[E-mail duplicado]:** `validate_email` rejeita com "E-mail já cadastrado." → 400. (`serializers.py:27-30`) 🟢
- **[`accept_terms` ausente/falso]:** "Aceite dos termos é obrigatório." → 400. (`serializers.py:22-25`) 🟢
- **[Usuário ADMIN]:** `ensure_welcome_conversation` retorna `None` — sem conversa criada. (`welcome.py:29-31`) 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `rest_framework_simplejwt` | Emissão de tokens | `RefreshToken.for_user` |
| `apps.common.exceptions.AppError` | Erros de validação envelopados | Handler global do DRF |
| `apps.audit.services.log.record` | Auditoria do evento | `USER_REGISTERED` — stub |
| `apps.conversations.services.welcome` | Onboarding pós-cadastro | `ensure_welcome_conversation` |
| `apps.common.logging_config.get_logger` | Log estruturado | `logger` da view |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Consentimento LGPD gravado no cadastro (`accepted_terms_at`) | `serializers.py:37` | 🟢 |
| Validação de senha por regex no serializer (duplicada no `AdminCreateUserSerializer`) | `serializers.py:6,16` | 🟢 |
| Auditoria por evento chamada, mas stub (ADR-007) | `audit/services/log.py:1-4` | 🟢 |
| Conversa de boas-vindas idempotente e pulada para ADMIN | `welcome.py:23-50` | 🟢 |
| Function-based view com `@api_view` (não ViewSet) | `views.py:19` | 🟢 |

## Riscos e Lacunas

- 🔴 `record()` do audit não persiste — sem trilha real do cadastro.
- 🟡 Sem throttling explícito na rota `register` (apenas throttling global anon 30/min) — risco de abuso/criação em massa.

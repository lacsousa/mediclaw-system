# Accounts / Me, Design Técnico

> Contrato operacional de **COMO** o perfil próprio é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/auth/me/` | — | `User` | 200, 401 | `IsAuthenticated` |
| PATCH | `/api/v1/auth/me/` | `{name?, email?}` | `User` | 200, 400, 401 | `IsAuthenticated` |
| DELETE | `/api/v1/auth/me/` | — | `204 No Content` | 204, 401 | `IsAuthenticated` |

## Fluxo Principal

1. Autenticação via JWT Bearer (`JWTAuthentication` global) resolve `request.user`. (`config/settings.py:116-118`) 🟢
2. **GET:** serializa `request.user` → `200 User`. (`views.py:71-72`) 🟢
3. **PATCH:** `MeUpdateSerializer(request.user, data=request.data, partial=True)` valida apenas os campos enviados. (`views.py:74-76`) 🟢
4. Se `name` presente → `user.first_name = name`; se `email` presente → valida unicidade e atribui. (`views.py:78-82`) 🟢
5. `user.save(update_fields=[...])` grava somente os campos alterados. (`views.py:84-86`) 🟢
6. **DELETE:** `user.delete()` → `204`; cascade via FK (`Patient.doctor`, `Conversation.doctor`, etc.). (`views.py:91-93`) 🟢

## Fluxos Alternativos

- **[E-mail duplicado no PATCH]:** `validate_email` exclui o próprio `pk` da checagem `iexact`; outro usuário com o mesmo e-mail → `ValidationError`. (`serializers.py:54-60`) 🟢
- **[Sem token / token inválido]:** 401 via simplejwt (`IsAuthenticated`). 🟡

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `rest_framework_simplejwt` | Autenticação do request | `JWTAuthentication` |
| `apps.common.exceptions.AppError` | Erros envelopados | Handler global |
| Modelos `patients`, `conversations`, `health_logs` | Cascade no delete | `on_delete=CASCADE` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| PATCH parcial via `partial=True` + `update_fields` | `views.py:74-86` | 🟢 |
| Unicidade de e-mail exceto próprio | `serializers.py:54-60` | 🟢 |
| Deleção em cascata de dados sensíveis (LGPD) | `views.py:92`; `patients/models.py:11` | 🟢 |
| Function-based view com `@api_view` + `@permission_classes` | `views.py:66-69` | 🟢 |

## Riscos e Lacunas

- 🟡 PATCH permite trocar e-mail a qualquer momento sem nova verificação de consentimento — comportamento do legado a validar com produto.
- 🟢 Cascade confirmado em `Patient.doctor` e `Conversation.doctor`; logs biométricos penduram no `Patient` (`health_logs`) — todos removidos ao deletar o usuário.

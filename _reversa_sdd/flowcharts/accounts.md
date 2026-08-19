# Fluxogramas — accounts

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. Register (POST `/api/v1/auth/register/`)

```mermaid
flowchart TD
    A[Request POST register] --> B{Serializer valida?}
    B -- não --> B1[400 VALIDATION_ERROR]
    B -- sim --> C[create_user: email minúsculo, hash senha, accepted_terms_at=now]
    C --> D[RefreshToken.for_user]
    D --> E[record USER_REGISTERED]
    E --> F{role = ADMIN?}
    F -- não --> G[ensure_welcome_conversation cria conversa Bem-vindo]
    F -- sim --> H[pula conversa]
    G --> I[201 access + refresh + user]
    H --> I
```

**Validações (RegisterSerializer):** senha ≥ 8 chars c/ letra e dígito 🟢 · `accept_terms` obrigatório 🟢 · email único (`iexact`) 🟢

## 2. Login (POST `/api/v1/auth/login/`)

```mermaid
flowchart TD
    A[Request POST login] --> B[email = request.data.email.lower]
    B --> C{authenticate OK?}
    C -- não --> C1[AppError INVALID_CREDENTIALS 401]
    C -- sim --> D{user.is_active?}
    D -- não --> C1
    D -- sim --> E[RefreshToken.for_user]
    E --> F[record LOGIN]
    F --> G[200 access + refresh + user]
```

**Observação:** falha de credencial e usuário inativo retornam o mesmo erro (não vaza qual campo está errado) 🟢

## 3. Me (GET/PATCH/DELETE `/api/v1/auth/me/`)

```mermaid
flowchart TD
    A[Request autenticado via JWT Bearer] --> B{Método?}
    B -- GET --> B1[200 UserSerializer user]
    B -- PATCH --> C{MeUpdateSerializer válido?}
    C -- não --> C1[400 VALIDATION_ERROR]
    C -- sim --> D{tem name?} --> E{tem email?}
    D -- sim --> D1[user.first_name = name]
    D -- não --> E
    E -- sim --> E1[user.email = email; valida unicidade exceto próprio]
    E -- não --> F[200 UserSerializer]
    D1 --> G[save update_fields]
    E1 --> G
    G --> F
    B -- DELETE --> H[user.delete cascade]
    H --> I[204 No Content]
```

## 4. Admin cria usuário (POST `/api/v1/admin/users/`)

```mermaid
flowchart TD
    A[Request POST /api/v1/admin/users/] --> B{IsAdminRole: role == ADMIN?}
    B -- não --> B1[403 FORBIDDEN]
    B -- sim --> C{AdminCreateUserSerializer válido?}
    C -- não --> C1[400 VALIDATION_ERROR]
    C -- sim --> D[create_user c/ role informado ou USER]
    D --> E[record ADMIN_CREATED_USER]
    E --> F{role = USER?}
    F -- sim --> G[ensure_welcome_conversation]
    F -- não --> H[pula]
    G --> I[201 UserSerializer]
    H --> I
```

## 5. persist_user_name (service — captura de nome via chat)

```mermaid
flowchart TD
    A[persist_user_name user_id, name] --> B[name.trim]
    B --> C{2 <= len <= 120?}
    C -- não --> C1[ValidationError]
    C -- sim --> D[User.objects.get pk=user_id]
    D --> E[user.first_name = name]
    E --> F[save update_fields=first_name]
    F --> G[return first_name]
```

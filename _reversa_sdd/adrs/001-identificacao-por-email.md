# ADR-001 — Identificação de usuário por e-mail (sem username)

**Status:** Aceito 🟢
**Data:** ~2026-06 (desde o primeiro commit)
**Fonte:** `accounts/models.py:24-32`, `accounts/serializers.py`, histórico Git (`f92d305` "First commit")

## Contexto

O projeto precisa de um identificador único e inequívoco para login. O `AbstractUser` do Django traz `username` como padrão, mas em contexto de plataforma de saúde o e-mail é o identificador natural (já é único por domínio e usado em comunicação com o usuário). Há risco de duplicidade de e-mails (case-insensitive) e de ambiguidade do `username`.

## Decisão

- `AUTH_USER_MODEL = "accounts.User"` com `USERNAME_FIELD = "email"` e `REQUIRED_FIELDS = []`.
- `email` é `unique=True` e **normalizado para minúsculo** no cadastro, login e update.
- `username` permanece como `CharField(blank=True)` herdado — **não é usado** como login.
- Política de senha própria: mín. 8 chars com letra e dígito.

## Consequências

- Login e recuperação são feitos por e-mail; `username` nunca é preenchido.
- `REQUIRED_FIELDS = []` simplifica `createsuperuser` (não pede campos extras).
- Unicidade de e-mail é case-insensitive (`iexact`) — dois cadastros com `A@x.com` e `a@x.com` colidem intencionalmente.

## Alternativas consideradas

- Usar `username` padrão do Django — rejeitado: identificador menos amigável e fora do contexto clínico.

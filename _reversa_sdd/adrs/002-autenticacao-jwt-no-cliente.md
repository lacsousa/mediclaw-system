# ADR-002 — Autenticação JWT Bearer mantida no cliente (revert de HttpOnly cookies)

**Status:** Aceito (por reversão) 🟡
**Data:** 2026-06-25 (tentativa e revert no mesmo dia)
**Fonte:** histórico Git — `52e2d2e` (migração para cookies HttpOnly), `c1c6ed9` (simplificação do refresh), `3ca2a7d` e `004e4e2` (reverts), estado atual do código (`react-painel/src/lib/auth.ts`, `src/context/AuthContext.tsx`, `apps/accounts/views.py`).

## Contexto

Havia um esforço para migrar a autenticação de `localStorage` para **cookies HttpOnly seguros** (mitiga roubo de token via XSS). O commit `52e2d2e` implementou a migração; `c1c6ed9` simplificou a hidratação e centralizou o refresh no interceptor do Axios. Ambos foram revertidos em `3ca2a7d` e `004e4e2`.

## Decisão

- Manter **JWT em memória/localStorage no cliente**, com `Authorization: Bearer <access>` no header.
- Tokens de access (30 min) e refresh (1 dia) retornados no corpo do login/register.
- O frontend gerencia a renovação via refresh token (interceptor).
- O endpoint de streaming SSE usa o access token no **query string** (`?token=`), pois `EventSource` não envia headers customizados.

## Consequências

- **Simplificação do backend:** views retornam `{access, refresh}` no corpo; sem CSRF/cookie handling.
- **Risco aceito:** token exposto no `localStorage` é vulnerável a XSS (mitigado por SPA sem conteúdo não confiável).
- **Stream expõe token no query string** — vaza em logs de proxy/access log (ver `permissions.md` P3). 🟡
- A motivação exata do revert **não está documentada** nos commits (mensagens de revert são vazias). Provável trade-off simplicidade × segurança para um MVP com prazo. 🟡 INFERIDO

## Alternativas consideradas

- Cookies HttpOnly (`52e2d2e`) — tentado e revertido.
- Cookies + rota de refresh centralizada no interceptor (`c1c6ed9`) — tentado e revertido.

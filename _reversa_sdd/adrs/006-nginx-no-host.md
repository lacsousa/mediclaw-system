# ADR-006 — Proxy reverso no host (Nginx) em vez de containerizado

**Status:** Aceito 🟢
**Data:** 2026-07-03 a 2026-08-06
**Fonte:** histórico Git — `3b05a1e` (migração para GitHub + infra de produção com Docker Compose e Let's Encrypt), `b5de41d` (Nginx no host substituindo Nginx/Certbot containerizado), `ee3fcf2` (split de vhosts; landing estática no domínio raiz), `8a7faaf` (sintaxe `listen ... http2` compatível com Nginx antigo do VPS), `8f681fa`/`4f36b79` (healthcheck com headers Host/X-Forwarded-Proto).

## Contexto

O projeto migrou do GitLab para GitHub (`3b05a1e`) e precisava de infraestrutura de produção. A primeira abordagem usava **Nginx + Certbot containerizados** no Docker Compose. No VPS, o Nginx disponível era antigo (sem `http2 on;`, exigindo `listen ... http2`) e a gestão de certificados no container agregava complexidade.

## Decisão

- **Nginx rodando no host** como único proxy reverso; Docker Compose expõe apenas os serviços internos (`django-api`, `react-painel`, `postgres`, `chroma`).
- **Dois vhosts:** domínio raiz serve a **landing estática** (`marketing/landing/`); subdomínio da API (`api.*`) proxia para o Django; o painel React em porta própria.
- TLS via **Let's Encrypt** gerenciado no host; `SECURE_PROXY_SSL_HEADER`/`USE_X_FORWARDED_HOST` no Django para não gerar redirect loop atrás do proxy.
- Healthcheck do Docker usa `Host` + `X-Forwarded-Proto` obrigatórios (validação de `ALLOWED_HOSTS`).

## Consequências

- Simplicidade operacional: certificados e proxy fora do Compose; release automation em script de deploy (`ee3fcf2`).
- Compatibilidade com o Nginx do VPS: sintaxe `listen ... http2` (o `http2 on;` não é suportado na versão instalada). 🟢
- Healthcheck validado com headers para não falhar no `ALLOWED_HOSTS` do Django.

## Alternativas consideradas

- Nginx + Certbot containerizados (abordagem inicial) — substituída por Nginx no host (`b5de41d`).
- Traefik/Caddy — não adotado (stack já estabelecida com Nginx).

# MediClaw System

Plataforma web com IA para apoio à **longevidade e bem-estar preventivo**.

**Restrição crítica:** A IA NUNCA emite diagnóstico médico ou prescrição. Toda resposta é educativa e acompanhada de disclaimer.

## Monorepo

| Pasta | Stack | Contexto |
|---|---|---|
| `django-api/` | Python 3.12 + Django 5.2 + DRF | @django-api/CLAUDE.md |
| `react-painel/` | Next.js + TypeScript | @react-painel/CLAUDE.md |

## Convenções Gerais

- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
- **Branch:** criar sempre a partir de `main`; nunca commitar direto na `main`
- **Segurança:** nunca logar PII (e-mail, mensagens de chat, dados biométricos)
- **LGPD:** dados de saúde são dados pessoais sensíveis — ver PROJECT-CONTEXT.md

## Como rodar

```bash
# Backend
cd django-api && uv run python manage.py runserver

# Frontend
cd react-painel && npm run dev
```

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


---

# Reversa

> Framework de Engenharia Reversa instalado neste projeto.

## Como usar

Use o fluxo adequado no chat:

- `/reversa` — descobrir e documentar um sistema existente
- `/reversa-new` — criar PRD e specs para um projeto novo
- `/reversa-forward` — implementar ou evoluir código a partir das specs
- `/reversa-migrate` — planejar a migração de um sistema legado
- `/reversa-docs` — gerar o mini-site visual da documentação
- `/reversa-agents-help` — consultar o catálogo completo de agentes

## Comportamento ao ativar

Quando o usuário digitar `/reversa` ou a palavra `reversa` sozinha em uma mensagem:

1. Ative o skill `reversa` disponível em `.claude/skills/reversa/SKILL.md`
2. Se não encontrar em `.claude/skills/`, tente `.agents/skills/reversa/SKILL.md`
3. Leia o SKILL.md na íntegra e siga exatamente as instruções do Reversa

## Regra não-negociável

Nunca apague, modifique ou sobrescreva arquivos pré-existentes do projeto legado.
O Reversa escreve apenas em `.reversa/`, `_reversa_sdd/`, `_reversa_docs/` e `_reversa_forward/`.

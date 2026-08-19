# Inventário do Projeto — MediClaw

> Gerado pelo **Scout** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO (extraído do código) | 🟡 INFERIDO | 🔴 LACUNA

## 1. Visão Geral

Plataforma web com IA para apoio à **longevidade e bem-estar preventivo**. Backend Django expõe APIs REST consumidas por um painel React (Next.js). A IA gera respostas educativas sobre dados biométricos (peso, sono, atividade) e não emite diagnóstico médico.

## 2. Estrutura de Pastas (top-level)

| Pasta | Papel | Tecnologia |
|---|---|---|
| `django-api/` | Backend | Python 3.12 + Django 5.2 + DRF |
| `react-painel/` | Painel web | Next.js 16 + React 19 + TypeScript |
| `marketing/` | Landing page estática | HTML/CSS |
| `nginx/` | Proxy reverso / vhosts | Nginx (VPS Hostinger) |
| `deploy.sh` | Automação de deploy | Bash + Docker Compose |

## 3. Backend — Apps Django (`django-api/apps/`)

| App | Responsabilidade | Endpoints (prefixo `api/v1/`) |
|---|---|---|
| `accounts` | Usuários, perfis, auth JWT | `/auth/register/`, `/auth/login/`, `/auth/refresh/`, `/auth/me/` |
| `patients` | Pacientes (CRUD por médico) | `/patients/`, `/patients/<id>/` |
| `health_logs` | Logs biométricos | `/health/weight|sleep|activity|nutrition/`, `/health/summary/` |
| `conversations` | Histórico de chat + streaming | `/conversations/`, `/conversations/<id>/`, `/conversations/<id>/messages/`, `/conversations/<id>/stream/` |
| `ai_engine` | Orquestrador IA, guardrails, skills, captura de dados | (sem rotas próprias — chamado via `conversations`) |
| `rag` | RAG: ingestão, vector store, retrieval | `/admin/knowledge/upload/`, `/admin/knowledge/`, `/admin/knowledge/<id>/status/`, `/admin/knowledge/<id>/` |
| `audit` | ActivityLog, métricas internas | `/admin/users/`, `/admin/metrics/` |
| `common` | Infra: exceptions, renderer, pagination, middleware | `/health/` |

## 4. Frontend — Rotas do Painel (`react-painel/src/app/`)

| Rota | Página |
|---|---|
| `/` | Home / landing da aplicação |
| `/login`, `/register` | Autenticação |
| `/chat`, `/chat/[id]` | Chat conversacional (com streaming SSE) |
| `/patients`, `/patients/[id]` | Gestão de pacientes + detalhes (tabs de saúde) |
| `/admin/metrics` | Métricas administrativas |
| `/conhecimento` | Base de conhecimento (RAG) |

## 5. Modelos de Dados (superficial — detalhe com o Data Master)

| App | Modelos |
|---|---|
| `accounts` | `User` (custom, `AUTH_USER_MODEL`, com `role` e `accepted_terms_at`) |
| `patients` | `Patient` (vinculado ao `doctor`/`User`) |
| `health_logs` | `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` |
| `conversations` | `Conversation`, `Message` (com `blocked_by_guardrail`, `metadata` JSON) |
| `rag` | `KnowledgeDocument` (status de ingestão, `chunk_count`) |

Banco: **PostgreSQL 16** (imagem `pgvector/pgvector:pg16` em produção).

## 6. Integrações Externas

| Integração | Uso |
|---|---|
| OpenAI API | Chat (`gpt-4o-mini`) + embeddings (`text-embedding-3-small`) |
| Google Gemini API | Alternativa de chat (`gemini-2.0-flash`) |
| ChromaDB | Vector store local (RAG) |
| Nginx + Let's Encrypt | TLS e proxy reverso no VPS |
| PostgreSQL (pgvector) | Banco principal (com extensão pgvector) |

## 7. Pontos de Entrada

- **Backend:** `django-api/manage.py`, `config/urls.py`, `config/settings.py`, `config/wsgi.py`, `config/asgi.py`, `entrypoint.prod.sh`
- **Frontend:** `react-painel/src/app/layout.tsx` (raiz App Router)
- **Landing:** `marketing/landing/index.html`
- **Infra:** `docker-compose.prod.yml`, `deploy.sh`, `Makefile`

## 8. CI/CD e Deploy

- **Nenhum CI/CD** (sem `.github/workflows`, Jenkinsfile ou GitLab CI) 🟢
- Deploy manual via `deploy.sh` (git pull + testes + `docker compose build/up`)
- Nginx do sistema (não containerizado) faz o proxy reverso — configs em `nginx/system/`
- Dois vhosts principais: `mediclaw.com.br` (landing + painel), `api.mediclaw.com.br` (API)

## 9. Docker / DevContainer

- `django-api/.devcontainer/` e `react-painel/.devcontainer/` — desenvolvimento containerizado
- `docker-compose.prod.yml` — stack de produção: `postgres` (pgvector), `django-api`, `react-painel`
- Portas: API `127.0.0.1:8000`, painel `127.0.0.1:3001` (a 3000 é usada por outro projeto no VPS)

## 10. Cobertura de Testes

| Área | Framework | Arquivos |
|---|---|---|
| Backend | pytest + pytest-django | 12 arquivos `test_*.py` (accounts, ai_engine, conversations, health_logs, rag) |
| Frontend | Vitest + Testing Library | 7 arquivos `.test.tsx/.ts` |

## 11. Observações do Scout

- 🟡 **Divergência spec × código:** as specs (PROJECT-CONTEXT.md) preveem `LLM_PROVIDER = openai | anthropic`, mas o código implementa **OpenAI + Gemini** (`apps/ai_engine/providers/`). O provider Anthropic não existe. Registrar para o Detective validar a intenção.
- 🟢 `main.py` do backend é apenas um stub ("Hello from django-api!") — não é entry point real.
- 🟢 `ai_engine/urls.py` é vazio — o orquestrador é invocado indiretamente via `conversations`.

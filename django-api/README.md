# MediClaw — Django API

Backend do MediClaw: API REST em Django + DRF com autenticação JWT, logs de saúde biométrica, assistente de IA com guardrails e RAG via ChromaDB.

---

## O que você vai encontrar pronto

| Epic | Status | O que está implementado |
|---|---|---|
| E1 — Foundation | ✅ | Settings, logging JSON, healthcheck, CI, middlewares |
| E2 — Auth & Users | ✅ | JWT, cadastro, login, refresh, perfil (`/me`) |
| E3 — Health Logs | ✅ | CRUD de peso/sono/atividade/nutrição + resumo agregado |
| E4 — AI Engine | ✅ | Providers OpenAI/Gemini, guardrails, skills (BMI, unidades), orquestrador com stream |
| E5 — RAG | ✅ | Ingestão PDF/TXT/MD, ChromaDB, retriever semântico, endpoints admin |
| E6 — Conversations | ✅ | CRUD de conversas, SSE streaming, conversa de boas-vindas, captura automática de dados de saúde via chat |
| E7 — Hardening | 🔜 | Pendente |

**137 testes passando** (`pytest tests/ -v`).

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 5.2 + Django REST Framework 3.16 |
| Auth | SimpleJWT (Bearer tokens) |
| Banco | PostgreSQL 16 |
| IA | OpenAI API ou Google Gemini (configurável via `LLM_PROVIDER`) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector Store | ChromaDB (persistido em disco) |
| Runtime | Python 3.12 |
| Testes | pytest + pytest-django |
| Linting | pre-commit + black |

---

## Setup local (sem devcontainer)

### Pré-requisitos

- Python 3.12+
- PostgreSQL rodando (local ou via Docker)
- Chave da API OpenAI **ou** Google Gemini

### 1. Clonar e criar ambiente virtual

```bash
git clone <repo>
cd django-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> Se usar `uv`: `uv sync`

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com os valores do seu ambiente. As variáveis obrigatórias são:

```env
SECRET_KEY=django-insecure-troque-por-algo-longo
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco
DB_NAME=mediclaw
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# AI — escolha um provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
CHAT_MODEL=gpt-4o-mini

# RAG
CHROMA_PERSIST_DIR=./chroma_data
EMBEDDING_MODEL=text-embedding-3-small
```

> Veja a seção [Variáveis de ambiente](#variáveis-de-ambiente) para a lista completa.

### 3. Criar banco e aplicar migrations

```bash
createdb mediclaw        # se ainda não existir
python manage.py migrate
```

### 4. Criar superusuário (opcional, para testar endpoints admin)

```bash
python manage.py createsuperuser
```

Ou via API (requer um usuário com `role=ADMIN` já criado):

```bash
# Não há endpoint público para promover usuário — use o shell
python manage.py shell -c "
from apps.accounts.models import User
u = User.objects.get(email='seu@email.com')
u.role = 'ADMIN'
u.save()
"
```

### 5. Rodar o servidor

```bash
python manage.py runserver
```

API disponível em `http://localhost:8000`.

---

## Setup com Devcontainer

```bash
# 1. Criar rede compartilhada (apenas uma vez)
docker network create mediclaw-dev-network

# 2. Subir só o Postgres (sem devcontainer)
docker compose -f .devcontainer/docker-compose.yml up postgres -d
# Postgres disponível em localhost:25432

# 3. Abrir no VS Code → "Reopen in Container"
```

O `postCreateCommand` instala dependências e aplica migrations automaticamente.

---

## Rodando os testes

```bash
# Todos os testes
pytest tests/ -v

# Por módulo
pytest tests/accounts/ -v
pytest tests/health_logs/ -v
pytest tests/ai_engine/ -v
pytest tests/rag/ -v
pytest tests/conversations/ -v
```

Resultado esperado: **137 passed**.

> Os testes de RAG e orquestrador mockam as chamadas ao OpenAI — nenhuma chave real é necessária para rodar a suite.

---

## Variáveis de ambiente

| Variável | Padrão | Obrigatória | Descrição |
|---|---|---|---|
| `SECRET_KEY` | — | **Sim** | Chave secreta Django |
| `DEBUG` | `False` | Não | Modo debug |
| `ALLOWED_HOSTS` | — | **Sim** | Hosts permitidos (vírgula) |
| `DB_NAME` | `mediclaw` | Não | Nome do banco |
| `DB_USER` | `postgres` | Não | Usuário do banco |
| `DB_PASSWORD` | `postgres` | Não | Senha do banco |
| `DB_HOST` | `localhost` | Não | Host do banco |
| `DB_PORT` | `5432` | Não | Porta do banco |
| `ACCESS_TOKEN_MINUTES` | `30` | Não | Validade do access token |
| `REFRESH_TOKEN_DAYS` | `1` | Não | Validade do refresh token |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Não | Origens permitidas (CORS) |
| `LLM_PROVIDER` | `openai` | Não | Provider de IA: `openai` ou `gemini` |
| `OPENAI_API_KEY` | — | Se `LLM_PROVIDER=openai` | Chave da API OpenAI |
| `CHAT_MODEL` | `gpt-4o-mini` | Não | Modelo de chat |
| `GOOGLE_API_KEY` | — | Se `LLM_PROVIDER=gemini` | Chave do Google Gemini |
| `HISTORY_WINDOW` | `6` | Não | Nº de mensagens anteriores enviadas ao LLM |
| `MAX_TOKENS_PER_RESPONSE` | `800` | Não | Limite de tokens por resposta |
| `CHROMA_PERSIST_DIR` | — | **Sim** (para RAG) | Diretório de persistência do ChromaDB |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Não | Modelo de embeddings (OpenAI) |
| `RAG_TOP_K` | `5` | Não | Número máximo de chunks recuperados |
| `RAG_MIN_SCORE` | `0.75` | Não | Score mínimo de similaridade |

---

## Endpoints implementados

Todas as respostas seguem o envelope:
```json
{ "data": <payload>, "error": null, "meta": {} }
```

### Sistema

| Método | URL | Auth | Descrição |
|---|---|---|---|
| `GET` | `/health` | Não | Status do DB e do vector store |

### Autenticação

| Método | URL | Auth | Descrição |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Não | Cadastro → retorna `{access, refresh, user}` |
| `POST` | `/api/v1/auth/login` | Não | Login → retorna `{access, refresh, user}` |
| `POST` | `/api/v1/auth/refresh` | Não | Renova access token |
| `GET` | `/api/v1/auth/me` | Bearer | Dados do usuário logado |
| `PATCH` | `/api/v1/auth/me` | Bearer | Atualizar nome e perfil |

### Logs de saúde

| Método | URL | Auth | Descrição |
|---|---|---|---|
| `GET/POST` | `/api/v1/health/weight/` | Bearer | Listar / registrar peso |
| `DELETE` | `/api/v1/health/weight/{id}/` | Bearer | Remover registro |
| `GET/POST` | `/api/v1/health/sleep/` | Bearer | Listar / registrar sono |
| `DELETE` | `/api/v1/health/sleep/{id}/` | Bearer | Remover registro |
| `GET/POST` | `/api/v1/health/activity/` | Bearer | Listar / registrar atividade |
| `DELETE` | `/api/v1/health/activity/{id}/` | Bearer | Remover registro |
| `GET/POST` | `/api/v1/health/nutrition/` | Bearer | Listar / registrar nota nutricional |
| `DELETE` | `/api/v1/health/nutrition/{id}/` | Bearer | Remover nota |
| `GET` | `/api/v1/health/summary` | Bearer | Resumo agregado (`?window=7\|30`) |

> Todos aceitam filtros `?from=<datetime>&to=<datetime>`.

### Conversas e chat

| Método | URL | Auth | Descrição |
|---|---|---|---|
| `POST` | `/api/v1/conversations/` | Bearer | Criar conversa |
| `GET` | `/api/v1/conversations/` | Bearer | Listar conversas paginadas (`?page=N`) |
| `GET` | `/api/v1/conversations/{id}/` | Bearer | Detalhe + mensagens |
| `DELETE` | `/api/v1/conversations/{id}/` | Bearer | Excluir conversa |
| `GET` | `/api/v1/conversations/{id}/stream` | `?token=` | SSE com o assistente (`?prompt=...&token=...`) |

O endpoint `/stream` usa Server-Sent Events. A autenticação é via query param `?token=` porque o browser não permite headers em `EventSource`. Eventos emitidos:

```
data: {"type": "token", "content": "..."}
data: {"type": "citation", "source": "...", "chunk_id": "..."}
data: {"type": "done", "tokens_used": 42, "blocked": false}
data: {"type": "error", "code": "...", "message": "..."}
```

### Base de conhecimento (admin)

> Requer usuário com `role=ADMIN`.

| Método | URL | Auth | Descrição |
|---|---|---|---|
| `POST` | `/api/v1/admin/knowledge/upload` | Bearer (admin) | Upload de PDF/TXT/MD (≤ 10 MB) |
| `GET` | `/api/v1/admin/knowledge/` | Bearer (admin) | Listar documentos indexados |
| `GET` | `/api/v1/admin/knowledge/{id}/status` | Bearer (admin) | Status de indexação |
| `DELETE` | `/api/v1/admin/knowledge/{id}` | Bearer (admin) | Remover documento e chunks do Chroma |

---

## Exemplos curl

### Healthcheck

```bash
curl http://localhost:8000/health
```

```json
{"data": {"status": "ok", "db": "ok", "vector_store": "ok", "version": "0.1.0"}, "error": null, "meta": {}}
```

### Cadastro

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@example.com", "password": "DevPass123", "name": "Dev", "accept_terms": true}'
```

### Login e salvar token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@example.com", "password": "DevPass123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")
```

### Criar conversa

```bash
curl -s -X POST http://localhost:8000/api/v1/conversations/ \
  -H "Authorization: Bearer $TOKEN"
```

### Upload de documento (admin)

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/knowledge/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@artigo.pdf" \
  -F "title=Artigo sobre saúde"
```

### Registrar peso

```bash
curl -s -X POST http://localhost:8000/api/v1/health/weight/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value_kg": 80.5, "measured_at": "2026-05-23T08:00:00Z"}'
```

### Resumo de saúde (entrada do prompt da IA)

```bash
curl -s "http://localhost:8000/api/v1/health/summary?window=7" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Arquitetura do AI Engine

```
query do usuário
      │
      ▼
 guardrail_pre          ← bloqueia diagnóstico / prescrição / urgência
      │
      ▼
 retriever.search()     ← busca chunks relevantes no ChromaDB
      │
      ▼
 health_summary()       ← agrega logs biométricos do usuário
      │
      ▼
 SYSTEM_PROMPT_TEMPLATE ← monta contexto com {rag_context} + {health_summary}
      │
      ▼
 LLM provider           ← OpenAI ou Gemini (configurável)
      │
      ▼
 guardrail_post         ← valida resposta gerada
      │
      ▼
 GenerateResult         ← content, tokens_used, blocked, citations
```

---

## Captura automática de dados de saúde via chat

O sistema não depende de formulários HTML para registrar dados biométricos. Quando o usuário envia uma mensagem no chat, o backend tenta extrair automaticamente dados de saúde usando `capture_from_message()`.

```
mensagem do usuário (texto natural)
      │
      ▼
 message_likely_has_health_data()   ← verifica keywords (kg, cm, dormi, etc.)
      │  não → ignora
      ▼
 parse_rules(text)                  ← regex para peso, altura, sexo, data nasc., sono, atividade, nutrição, nome
      │
      ▼
 has_actionable_data()?             ← verifica se algo foi extraído
      │  não → tenta extração via LLM
      ▼
 persist(user_id, data)             ← salva WeightLog / SleepLog / ActivityLog / NutritionNote / Profile / first_name
      │
      ▼
 CaptureResult                      ← {saved, errors, still_missing} — incluído no metadata SSE do done event
```

**`UserReadiness`** rastreia o que ainda falta no perfil do usuário (`birth_date`, `biological_sex`, `height_cm`, peso inicial). É usada para direcionar o prompt e a conversa de boas-vindas.

**Conversa de boas-vindas** (`ensure_welcome_conversation`) é criada automaticamente no cadastro, com uma mensagem do assistente pedindo os dados em linguagem natural. Exemplo de resposta esperada do usuário:

> "Me chamo Maria, tenho 1,75 m, 80 kg, nasci em 15/03/1990 e sou mulher."

---

## Estrutura do projeto

```
django-api/
├── apps/
│   ├── accounts/           # E2 — Auth & Users
│   │   ├── models.py       # User (email login, role), Profile
│   │   ├── serializers.py
│   │   └── views.py        # register, login, me, admin_create_user
│   ├── common/             # E1 — Utilitários compartilhados
│   │   ├── exceptions.py   # AppError, envelope_exception_handler
│   │   ├── renderers.py    # EnvelopeJSONRenderer → {data, error, meta}
│   │   ├── permissions.py  # IsAdminRole, IsOwner
│   │   ├── middleware.py   # RequestIDMiddleware
│   │   └── views.py        # GET /health (DB + vector store)
│   ├── health_logs/        # E3 — Core API
│   │   ├── models.py       # WeightLog, SleepLog, ActivityLog, NutritionNote
│   │   ├── views.py        # 4 ViewSets + health_summary
│   │   └── services/
│   │       └── aggregate.py  # summarize(user_id, window_days)
│   ├── ai_engine/          # E4 — AI Engine
│   │   ├── guardrails.py   # check_input / check_output (regex determinístico)
│   │   ├── orchestrator.py # generate() + generate_stream()
│   │   ├── prompts.py      # SYSTEM_PROMPT_TEMPLATE
│   │   ├── providers/      # OpenAIProvider, GeminiProvider (Protocol)
│   │   ├── services/
│   │   │   ├── capture_models.py      # ExtractedUserData, CaptureResult (Pydantic)
│   │   │   ├── capture_rules.py       # parse_rules() + regex patterns
│   │   │   ├── data_extraction_llm.py # extração via LLM como fallback
│   │   │   └── user_data_capture.py   # capture_from_message(user_id, text) → CaptureResult
│   │   └── skills/         # bmi, unit_convert, health_summary, user_readiness
│   ├── rag/                # E5 — RAG
│   │   ├── vector_store.py # ChromaDB singleton (CHROMA_PERSIST_DIR)
│   │   ├── ingestion.py    # ingest(document, file_bytes) — PDF/TXT/MD
│   │   ├── retriever.py    # search(query, k, min_score) → list[dict]
│   │   ├── models.py       # KnowledgeDocument (PROCESSING/INDEXED/ERROR)
│   │   └── views.py        # upload, list, status, delete (admin)
│   ├── conversations/      # E6 — Chat
│   │   ├── models.py       # Conversation, Message
│   │   ├── views.py        # list_create, detail, stream (SSE)
│   │   └── services/
│   │       └── welcome.py  # ensure_welcome_conversation(user) → cria onboarding na 1ª vez
│   └── audit/              # Stub — será expandido em E7
│       └── services/log.py # record() — placeholder
├── config/
│   ├── settings.py
│   └── urls.py
├── tests/
│   ├── conftest.py          # fixtures: api_client, user, other_user, auth_client
│   ├── accounts/            # 13 testes
│   ├── health_logs/         # 5 testes
│   ├── ai_engine/           # 78 testes (guardrails + skills + orquestrador + user_data_capture + user_readiness)
│   ├── rag/                 # 15 testes (ingestão + retriever + views)
│   └── conversations/       # 26 testes (CRUD + stream + welcome)
├── specs/
│   ├── epics/               # Especificações técnicas por épico
│   └── TASKS.md             # Roadmap executável com checkpoints
├── .env.example
└── pytest.ini
```

---

## Pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

Hooks: `black` (formatação), `trailing-whitespace`, `end-of-file-fixer`.

---

## Troubleshooting

**`Missing required env: SECRET_KEY`**
```bash
cp .env.example .env   # e preencha SECRET_KEY
```

**`Missing required env: CHROMA_PERSIST_DIR`**
```bash
# Adicione ao .env:
CHROMA_PERSIST_DIR=./chroma_data
```

**Erro de conexão com banco**
```bash
docker compose -f .devcontainer/docker-compose.yml up postgres -d
# DB_HOST=localhost, DB_PORT=25432
```

**Vector store retorna `error` no /health**
- Verifique se `CHROMA_PERSIST_DIR` existe e tem permissão de escrita
- O diretório é criado automaticamente na primeira requisição

**`OPENAI_API_KEY` inválida — chat não funciona**
- Os testes não exigem chave real (tudo mockado)
- Para usar o chat em runtime, configure `OPENAI_API_KEY=sk-...` no `.env`

---

## Roadmap

| Epic | Status | Descrição |
|---|---|---|
| E1 — Foundation | ✅ | Settings, common, healthcheck, CI |
| E2 — Auth & Users | ✅ | JWT, cadastro, login, perfil |
| E3 — Health Logs | ✅ | CRUD biométrico + service de agregação |
| E4 — AI Engine | ✅ | Providers OpenAI/Gemini, guardrails, skills, orquestrador |
| E5 — RAG | ✅ | ChromaDB, ingestão PDF/TXT/MD, retriever semântico, endpoints admin |
| E6 — Conversations | ✅ | CRUD de conversas, SSE streaming, conversa de boas-vindas, captura automática de dados de saúde via chat |
| E7 — Hardening | 🔜 | Testes de integração E2E, hardening de segurança, docker compose prod |

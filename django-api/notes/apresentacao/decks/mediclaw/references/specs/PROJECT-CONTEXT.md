# MediClaw — Project Context

> Arquivo de contexto para agentes de IA e desenvolvedores.
> Leia este arquivo antes de qualquer implementação.
> **Escopo:** Backend (Django + DRF). O Frontend React é tratado como cliente externo do backend.

---

## O que é o MediClaw

Plataforma web com IA para apoio à **longevidade e bem-estar preventivo**. Backend Django expõe APIs REST para um cliente React, com chat conversacional sobre dados biométricos do usuário (peso, sono, atividade) e recomendações educativas embasadas em literatura científica via RAG.

**Restrição crítica:** A IA **NUNCA** emite diagnóstico médico ou prescrição. Toda resposta é educativa, preventiva e acompanhada de disclaimer.

---

## Stack (não negociável no MVP)

| Camada | Tecnologia | Notas |
|---|---|---|
| Linguagem | Python 3.12 | Versão suportada por Django 5.2 |
| Framework | Django 5.2 + Django REST Framework 3.16 | Não usar FastAPI/Flask |
| Auth | `djangorestframework-simplejwt` 5.5 | JWT com access + refresh |
| Banco | PostgreSQL 16 | Driver `psycopg[binary]` 3.2 |
| ORM | Django ORM | Sem SQLAlchemy |
| LLM Provider | OpenAI **ou** Anthropic | Configurável via env (`LLM_PROVIDER`) |
| Orquestração IA | LangChain (Python) 0.3 | Camada de orquestração e RAG |
| Vector Store | ChromaDB (local, MVP) | Migração futura para `pgvector` |
| CORS | `django-cors-headers` 4.7 | Restrito a origens autorizadas |
| Env | `python-dotenv` 1.1 | Sem `os.getenv` direto fora de `settings.py` |
| Lint/Format | `black` + `pre-commit` | Já configurado no repo |
| Infra | Docker + Docker Compose | DevContainer já presente |

---

## Estrutura do Projeto

```
mediclaw/
├── config/                    # Projeto Django (settings, urls, wsgi/asgi)
├── apps/
│   ├── accounts/              # Usuários, perfis, autenticação JWT
│   ├── health_logs/           # Logs biométricos (peso, sono, atividade)
│   ├── conversations/         # Histórico de chat com a IA
│   ├── ai_engine/             # Orquestrador, prompts, guardrails, skills
│   ├── rag/                   # Ingestão de documentos, vector store, retrieval
│   └── audit/                 # ActivityLog, métricas internas
├── knowledge_base/            # Documentos fonte (PDF, MD, TXT) para indexação
├── chroma_data/               # Persistência do ChromaDB (volume Docker)
├── tests/                     # Testes pytest (unitários + integração)
├── specs/                     # Esta documentação BMAD
├── manage.py
├── requirements.txt
├── docker-compose.yml         # (em .devcontainer/ no MVP)
└── .env.example
```

---

## Convenções de Código

### Backend

- **Apps Django:** uma responsabilidade por app. Modelos em `models.py`, lógica em `services/`, endpoints em `views.py`, schemas em `serializers.py`, rotas em `urls.py`.
- **Service layer:** toda lógica de negócio em `apps/<app>/services/<dominio>.py`. Views só fazem orquestração HTTP, validação e response.
- **Serializers DRF:** sempre validar entrada e moldar saída — nunca retornar `model_to_dict` cru.
- **Erros:** usar exceções DRF customizadas em `apps/common/exceptions.py` com `code` e `default_detail`.
- **Respostas:** padrão `{ "data": ..., "error": null, "meta": {...} }` via renderer customizado.
- **Settings:** apenas `config/settings.py` lê env vars. Outros módulos importam de `django.conf.settings`.
- **Logs:** `logging.getLogger(__name__)`. Nunca logar conteúdo de mensagens do chat ou dados sensíveis de saúde.
- **Migrations:** sempre commitadas. Nunca editar migrations já aplicadas em produção.

### Geral

- **Type hints:** obrigatório em funções de service layer e camada de IA.
- **Comentários:** apenas quando o "porquê" não é óbvio — sem comentários de "o que".
- **Testes:** `pytest` + `pytest-django`. Banco de teste real (não mockar Postgres). Mockar apenas chamadas LLM externas.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`).

---

## Modelos de IA e Limites

| Uso | Modelo padrão | Limite |
|---|---|---|
| Chat (geração) | `gpt-4o-mini` (OpenAI) ou `claude-haiku-4-5` (Anthropic) | 800 tokens/resposta |
| Embeddings | `text-embedding-3-small` (OpenAI) | 1536 dim |
| Histórico no prompt | — | Últimas 6 mensagens |
| Mensagens por conversa | — | Máx 50 |
| RAG chunks recuperados | — | Top-5, score ≥ 0.75 |
| Skills (function calling) | — | Definidas em `apps/ai_engine/skills/` |

---

## Padrão de Resposta da API

```json
// Sucesso
{ "data": { "...": "..." }, "error": null, "meta": { "total": 10, "page": 1 } }

// Erro
{ "data": null, "error": { "code": "SNAKE_CASE_CODE", "message": "Mensagem legível" } }
```

**Codes de erro padrão:**

- `INVALID_CREDENTIALS` — Login falhou
- `EMAIL_ALREADY_EXISTS` — Cadastro duplicado
- `MISSING_TOKEN` — Rota autenticada sem token
- `INVALID_TOKEN` — Token inválido ou expirado
- `TOKEN_EXPIRED` — Access token expirou (cliente deve usar refresh)
- `FORBIDDEN` — Permissão insuficiente
- `NOT_FOUND` — Recurso não encontrado
- `VALIDATION_ERROR` — Payload inválido (detalhes em `error.details`)
- `CONVERSATION_LIMIT_REACHED` — Conversa com 50 mensagens
- `GUARDRAIL_BLOCKED` — Solicitação bloqueada por guardrail (ex.: pedido de diagnóstico)
- `LLM_PROVIDER_ERROR` — Erro upstream do provedor de LLM
- `FILE_TOO_LARGE` — Upload > 10MB
- `INVALID_FILE_TYPE` — Tipo de arquivo não aceito

---

## Segurança — Checklist por Feature

Antes de fazer merge:

- [ ] Inputs validados via Serializer DRF (nunca usar `request.data` cru)
- [ ] Rotas privadas com `permission_classes = [IsAuthenticated]`
- [ ] Rotas admin com `IsAdminUser` ou permission custom
- [ ] Sem `print` ou `logger.info` com PII (e-mail, mensagens, dados biométricos)
- [ ] Sem raw SQL não parametrizado (usar Django ORM ou `params=`)
- [ ] Sem secrets em código-fonte ou em logs
- [ ] Throttling DRF ativo na rota (anon + user)

---

## LGPD — Regras Inegociáveis

Dados de saúde são **dados pessoais sensíveis** (LGPD Art. 11). O MVP segue:

- **Disclaimer médico** obrigatório em respostas com viés clínico (injetado pelo guardrail no system prompt)
- **Consentimento LGPD** explícito no cadastro (campo `accepted_terms_at` obrigatório)
- **Cascade delete:** ao deletar usuário, todas as conversas, mensagens e logs de saúde devem ser removidos
- **Minimização:** não coletar nem logar dado além do necessário para a funcionalidade
- **Retenção:** conversas retidas por 90 dias após última atividade (configurável via env)
- **Sem log do conteúdo das mensagens** em produção (apenas metadados: `conversation_id`, `tokens_used`, `latency_ms`)

---

## Variáveis de Ambiente (`.env`)

```bash
# Django
SECRET_KEY="mude-em-producao-min-50-chars"
DEBUG=False
ALLOWED_HOSTS="localhost,127.0.0.1,api.mediclaw.com"

# Banco
DB_NAME=mediclaw
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

# JWT
ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=1

# CORS
CORS_ALLOWED_ORIGINS="http://localhost:3000"

# IA
LLM_PROVIDER="openai"          # openai | anthropic
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
EMBEDDING_MODEL="text-embedding-3-small"
CHAT_MODEL="gpt-4o-mini"

# RAG
CHROMA_PERSIST_DIR="/app/chroma_data"
RAG_TOP_K=5
RAG_MIN_SCORE=0.75

# Limites
MAX_TOKENS_PER_RESPONSE=800
MAX_MESSAGES_PER_CONVERSATION=50
HISTORY_WINDOW=6
CONVERSATION_RETENTION_DAYS=90

# Admin seed
ADMIN_EMAIL="admin@mediclaw.com"
ADMIN_PASSWORD="Admin123!"
```

---

## Como Rodar Localmente

```bash
# 1. DevContainer (recomendado)
# Abrir a pasta no VS Code → Reopen in Container

# 2. Manual
docker compose -f .devcontainer/docker-compose.yml up -d postgres
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

---

## Ordem de Implementação Recomendada

Seguir o [TASKS.md](TASKS.md) em ordem. Sequência crítica:

```
E1 (Foundation) → E2 (Auth) → E3 (Core API: health logs + conversations) →
E4 (AI Engine + Guardrails) → E5 (RAG) → E6 (Testes & Avaliação)
```

**Regra:** Cada épico deve estar funcional e com testes passando antes de iniciar o próximo.

---

*Este arquivo deve ser lido por qualquer agente ou desenvolvedor antes de iniciar trabalho no projeto.*

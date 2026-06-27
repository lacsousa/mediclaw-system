# MediClaw — Architecture Document

> Versão: 1.0 | Data: 2026-05-07
> Referência: [MVP.md](MVP.md) | [PRD.md](PRD.md) | [TASKS.md](TASKS.md)
> **Escopo:** Backend Django. Frontend React é cliente externo.

---

## Visão Geral

Backend monolítico Django + DRF servindo APIs REST e SSE para um cliente React. PostgreSQL como banco relacional. ChromaDB local como vector store. LangChain Python orquestra o pipeline de RAG e tool calling. Provider de LLM é configurável (OpenAI ou Anthropic) atrás de uma interface comum.

```
React Client ──HTTPS──▶  Django/DRF (uvicorn ASGI)
                              │
            ┌─────────────────┼──────────────────────────┐
            │                 │                          │
            ▼                 ▼                          ▼
       PostgreSQL        ai_engine                    rag
       (ORM models)   (orchestrator,              (ingestion,
                       guardrails,                  retriever)
                       skills)                          │
                          │                             │
                          ▼                             ▼
                   LLM Provider                    ChromaDB
                  (OpenAI/Anthropic)              (volume Docker)
```

---

## Architectural Decision Records (ADRs)

### ADR-01: Django + DRF como framework principal
- **Decisão:** Django 5.2 + Django REST Framework 3.16
- **Por quê:** Maturidade, admin embutido para CRUD de KB, ORM robusto, ecossistema Python alinhado com IA/ML
- **Trade-off:** Mais opinionado que FastAPI; ASGI necessário para SSE eficiente
- **Alternativa descartada:** FastAPI — exigiria mais código boilerplate para auth/admin/migrations no MVP

### ADR-02: PostgreSQL como banco relacional
- **Decisão:** PostgreSQL 16 com driver `psycopg[binary]` 3.x
- **Por quê:** Robustez, JSONB para `metadata`, e path direto para `pgvector` na fase 2
- **Trade-off:** Mais infra que SQLite, mas DevContainer já trata
- **Migração:** ChromaDB → `pgvector` extension reaproveitando o mesmo Postgres

### ADR-03: ChromaDB local como vector store do MVP
- **Decisão:** `chromadb` em modo persistente apontando para volume Docker
- **Por quê:** Zero infra externa (sem Pinecone/Weaviate), API simples
- **Trade-off:** Não escala horizontalmente; OK para MVP single-node
- **Migração:** Fase 2 → `pgvector` no PostgreSQL existente. `LangChain` abstrai a troca via `Chroma` → `PGVector`

### ADR-04: JWT via `djangorestframework-simplejwt`
- **Decisão:** Access token 30min + refresh token 1d, sem blacklist no MVP
- **Por quê:** Stateless, sem Redis, integração nativa com DRF
- **Trade-off:** Logout não invalida access ativo até expiração; aceitável no MVP
- **Migração:** Fase 2 → blacklist via `simplejwt` + Redis para revogação imediata

### ADR-05: SSE para streaming
- **Decisão:** Server-Sent Events sobre HTTP, servido via ASGI (uvicorn)
- **Por quê:** Nativo no browser (`EventSource`), unidirecional bastante para chat
- **Trade-off:** Em WSGI o streaming é instável; obriga ASGI em produção. EventSource não suporta headers customizados → token via query string com TTL curto
- **Alternativa descartada:** WebSocket — overhead de protocolo desnecessário

### ADR-06: Provider-agnóstico de LLM
- **Decisão:** Interface `LLMProvider` em `apps/ai_engine/providers/base.py` com implementações OpenAI e Anthropic
- **Por quê:** Permite trocar provedor via env, comparar custo/qualidade, evitar lock-in
- **Trade-off:** Pequena camada de abstração extra; recursos exclusivos de um provedor (ex.: prompt caching) precisam ser explicitamente expostos na interface
- **Migração:** Adicionar provedores (Bedrock, Vertex, local) implementando a mesma interface

### ADR-07: LangChain Python como camada de orquestração
- **Decisão:** `langchain` 0.3 + `langchain-openai` / `langchain-anthropic` / `langchain-community`
- **Por quê:** Splitters, loaders, retrievers e integração com Chroma já prontos
- **Trade-off:** Risco de churn na API entre minor versions; isolar uso em `apps/ai_engine` e `apps/rag`

### ADR-08: Guardrails determinísticos antes de LLM
- **Decisão:** Filtros por keyword/regex em `apps/ai_engine/guardrails.py` aplicados pré e pós LLM
- **Por quê:** Latência e custo zero; reproduzível; auditável
- **Trade-off:** Falsos positivos exigem manutenção da lista; modelos de classificação ML ficam para fase 2

### ADR-09: Indexação RAG síncrona no MVP
- **Decisão:** Upload do admin processa o documento na própria requisição (timeout 60s)
- **Por quê:** Sem fila/Celery no MVP. Documentos pequenos (≤ 10MB) cabem nesse orçamento
- **Trade-off:** Bloqueia o admin durante a ingestão; UX aceitável
- **Migração:** Celery + Redis na fase 2 com status via polling em `/status` (já contemplado no contrato da API)

### ADR-10: Renderer customizado `{ data, error, meta }`
- **Decisão:** `apps/common/renderers.py::EnvelopeJSONRenderer` aplicado por padrão no DRF
- **Por quê:** Cliente único e consistente independente do endpoint
- **Trade-off:** Diverge do default do DRF; documentar em `PROJECT-CONTEXT.md`

---

## Stack Detalhada

### Backend

| Camada | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12 |
| Framework | Django | 5.2.x |
| API | Django REST Framework | 3.16.x |
| Auth | `djangorestframework-simplejwt` | 5.5.x |
| ORM | Django ORM | (built-in) |
| Banco | PostgreSQL | 16 |
| Driver | `psycopg[binary]` | 3.2.x |
| CORS | `django-cors-headers` | 4.7.x |
| Env | `python-dotenv` | 1.1.x |
| LLM SDK | `openai` ≥ 1.30 / `anthropic` ≥ 0.34 | — |
| Orquestração IA | `langchain` | 0.3.x |
| Vector Store | `chromadb` | 0.5.x |
| PDF Loader | `pypdf` | ≥ 4.0 |
| Validação extra | `pydantic` | ≥ 2.7 (skills schemas) |
| Server (prod) | `uvicorn[standard]` | ≥ 0.30 |
| Testes | `pytest` + `pytest-django` | 8.x / 4.x |
| Lint/Format | `black` + `pre-commit` | 25.1 / 4.2 |

### Infra

| Item | Tecnologia |
|---|---|
| Container | Docker + Docker Compose |
| Orquestração local | DevContainer (já no repo) |
| Volumes | `pgdata`, `chroma_data`, `knowledge_base` |
| CI | GitLab CI (`.gitlab-ci.yml` já presente) |
| Deploy alvo | VPS single-node + reverse proxy (Nginx) |

---

## Estrutura de Módulos do Backend

```
config/
├── settings.py        # Lê .env, valida obrigatórios, define DRF, JWT, CORS, LOGGING
├── urls.py            # Rotas globais; inclui apps via include()
├── asgi.py            # Necessário para SSE em prod
└── wsgi.py            # Mantido para tooling, mas não usado em prod

apps/
├── common/
│   ├── exceptions.py        # AppError, GuardrailBlockedError, LLMProviderError
│   ├── renderers.py         # EnvelopeJSONRenderer
│   ├── pagination.py        # PageNumberPagination padrão
│   ├── permissions.py       # IsAdminRole, IsOwner
│   └── middleware.py        # request_id, structured logging
│
├── accounts/
│   ├── models.py            # User (AbstractUser), Profile
│   ├── managers.py
│   ├── serializers.py
│   ├── views.py             # register, login, me, refresh
│   ├── urls.py
│   └── services/auth.py
│
├── health_logs/
│   ├── models.py            # WeightLog, SleepLog, ActivityLog, NutritionNote
│   ├── serializers.py
│   ├── views.py             # ViewSets para CRUD
│   ├── urls.py
│   └── services/aggregate.py  # summary(user_id, window)
│
├── conversations/
│   ├── models.py            # Conversation, Message
│   ├── serializers.py
│   ├── views.py             # CRUD + sse stream view
│   ├── urls.py
│   └── services/chat.py     # send_message(user, conv, content) → Message
│
├── ai_engine/
│   ├── orchestrator.py      # generate(user_id, conv_id, query)
│   ├── prompts.py           # SYSTEM_PROMPT, templates
│   ├── guardrails.py        # check_input, check_output, KEYWORDS, REGEX
│   ├── skills/
│   │   ├── __init__.py      # SKILLS = [calculate_bmi, convert_units]
│   │   ├── bmi.py
│   │   ├── unit_convert.py
│   │   └── health_summary.py
│   └── providers/
│       ├── base.py          # class LLMProvider (Protocol)
│       ├── openai_provider.py
│       └── anthropic_provider.py
│
├── rag/
│   ├── models.py            # KnowledgeDocument
│   ├── vector_store.py      # get_collection() singleton
│   ├── ingestion.py         # ingest(file) → status, chunk_count
│   ├── retriever.py         # search(query, k, min_score)
│   ├── serializers.py
│   ├── views.py             # admin upload, list, delete, status
│   └── urls.py
│
└── audit/
    ├── models.py            # ActivityLog
    ├── services/log.py      # record(action, user, metadata)
    ├── serializers.py
    ├── views.py             # admin metrics, logs
    └── urls.py
```

---

## Fluxo de Dados — Chat com RAG e Guardrails

```
1. POST /api/v1/conversations/{id}/messages  Authorization: Bearer <jwt>
   Body: { "content": "Como melhorar meu sono?" }

2. View autentica → resolve User → busca Conversation (verifica ownership)

3. Chama services.chat.send_message(user, conv, content):
   a. Persiste Message(role=USER)
   b. Chama ai_engine.orchestrator.generate(user.id, conv.id, content)

4. orchestrator.generate:
   a. guardrails.check_input(content) → se bloqueado, retorna mensagem educativa pré-definida
   b. retriever.search(content, k=5, min_score=0.75) → list[Chunk]
   c. skills.health_summary(user.id) → dict (média 7d sono, peso, etc.)
   d. Monta mensagens:
      - system: SYSTEM_PROMPT.format(context=chunks, health_summary=summary)
      - history: últimas 6 mensagens da conversa
      - user: content
   e. provider.stream(messages, max_tokens=800) → Iterator[str]
   f. Coleta tokens; ao final, guardrails.check_output(text) → injeta disclaimer ou bloqueia/regenera

5. Persiste Message(role=ASSISTANT, content, tokens_used, metadata={citations:[...]})

6. audit.log(action="MESSAGE_SENT", user, {tokens_used, blocked, latency_ms})

7. Retorna a Message do assistente serializada
```

### Streaming SSE (rota separada)

```
GET /api/v1/conversations/{id}/stream?prompt=<encoded>&token=<jwt>
  ↓ ASGIView async
  ↓ Mesma orquestração mas yield token a token via StreamingHttpResponse
  ↓ data: {"type":"token","content":"..."}\n\n   # por chunk LLM
  ↓ data: {"type":"citation","source":"...","chunk_id":"..."}\n\n  # quando aplicável
  ↓ data: {"type":"done","tokens_used":N,"blocked":false}\n\n
```

---

## Schema de Banco (Django ORM)

> **Epic 8 (Patient Management):** `Profile` removido; nova entidade `Patient` agrupa dados do paciente.
> FK `user` em health logs e conversas migrada — ver [epic-8-patient.md](epics/epic-8-patient.md).

```python
# apps/accounts/models.py
class User(AbstractUser):
    email = EmailField(unique=True)
    role = CharField(max_length=10, choices=[("USER","USER"),("ADMIN","ADMIN")], default="USER")
    accepted_terms_at = DateTimeField(null=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    # Profile removido em Epic 8 — campos migrados para Patient

# apps/patients/models.py  (novo em Epic 8)
class Patient(Model):
    doctor = ForeignKey(User, on_delete=CASCADE, related_name="patients")
    first_name = CharField(max_length=120)
    birth_date = DateField(null=True)
    biological_sex = CharField(max_length=10, null=True, choices=[("M","M"),("F","F"),("OTHER","OTHER")])
    height_cm = PositiveSmallIntegerField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    class Meta:
        constraints = [UniqueConstraint(fields=["doctor","first_name","birth_date"],
                                        condition=Q(birth_date__isnull=False),
                                        name="unique_patient_name_dob_per_doctor")]
        indexes = [Index(fields=["doctor","first_name"]), Index(fields=["doctor","-created_at"])]

# apps/health_logs/models.py  (FK: user → patient em Epic 8)
class WeightLog(Model):
    patient = ForeignKey("patients.Patient", on_delete=CASCADE, related_name="weight_logs")
    value_kg = DecimalField(max_digits=5, decimal_places=2)
    measured_at = DateTimeField()
    class Meta:
        indexes = [Index(fields=["patient", "-measured_at"])]
        ordering = ["-measured_at"]

class SleepLog(Model):
    patient = ForeignKey("patients.Patient", on_delete=CASCADE, related_name="sleep_logs")
    duration_hours = DecimalField(max_digits=4, decimal_places=2)
    quality_score = PositiveSmallIntegerField()
    started_at = DateTimeField()
    class Meta:
        indexes = [Index(fields=["patient", "-started_at"])]

class ActivityLog(Model):
    patient = ForeignKey("patients.Patient", on_delete=CASCADE, related_name="activity_logs")
    type = CharField(max_length=40)
    duration_min = PositiveSmallIntegerField()
    performed_at = DateTimeField()
    class Meta:
        indexes = [Index(fields=["patient", "-performed_at"])]

class NutritionNote(Model):
    patient = ForeignKey("patients.Patient", on_delete=CASCADE, related_name="nutrition_notes")
    note = TextField()
    logged_at = DateTimeField()
    class Meta:
        indexes = [Index(fields=["patient", "-logged_at"])]

# apps/conversations/models.py  (Epic 8: user→doctor, +patient, +deleted_at)
class Conversation(Model):
    doctor = ForeignKey(User, on_delete=CASCADE, related_name="conversations")   # renomeado de 'user'
    patient = ForeignKey("patients.Patient", on_delete=SET_NULL,                  # novo
                         null=True, blank=True, related_name="conversations")
    title = CharField(max_length=120, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    deleted_at = DateTimeField(null=True, blank=True)  # soft delete (Epic 8)
    class Meta:
        indexes = [Index(fields=["doctor","-updated_at"]), Index(fields=["patient","-updated_at"])]

class Message(Model):
    ROLE_CHOICES = [("USER","USER"),("ASSISTANT","ASSISTANT"),("SYSTEM","SYSTEM")]
    conversation = ForeignKey(Conversation, on_delete=CASCADE, related_name="messages")
    role = CharField(max_length=10, choices=ROLE_CHOICES)
    content = TextField()
    tokens_used = PositiveIntegerField(null=True)
    blocked_by_guardrail = BooleanField(default=False)
    metadata = JSONField(default=dict)  # citations, latency, model
    created_at = DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [Index(fields=["conversation", "created_at"])]

# apps/rag/models.py
class KnowledgeDocument(Model):
    STATUS = [("PROCESSING","PROCESSING"),("INDEXED","INDEXED"),("ERROR","ERROR")]
    title = CharField(max_length=200)
    file_name = CharField(max_length=255)
    mime_type = CharField(max_length=80)
    status = CharField(max_length=12, choices=STATUS, default="PROCESSING")
    chunk_count = PositiveIntegerField(null=True)
    error_message = TextField(blank=True)
    uploaded_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# apps/audit/models.py
class ActivityLog(Model):
    user = ForeignKey(User, on_delete=SET_NULL, null=True, related_name="audit_logs")
    action = CharField(max_length=60)
    metadata = JSONField(default=dict)
    created_at = DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [Index(fields=["user", "-created_at"]), Index(fields=["action", "-created_at"])]
```

### Migrations

- Cada app gera suas migrations com `python manage.py makemigrations`
- Sempre commitadas
- Para rollback de schema, gerar nova migration reversa (não editar histórico aplicado)

---

## Configuração do DRF

```python
# config/settings.py (resumo)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["apps.common.renderers.EnvelopeJSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "60/min",
        "chat": "10/min",
    },
    "EXCEPTION_HANDLER": "apps.common.exceptions.envelope_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ["ACCESS_TOKEN_MINUTES"])),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ["REFRESH_TOKEN_DAYS"])),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

---

## Segurança

| Vetor | Mitigação |
|---|---|
| SQL Injection | Django ORM parametrizado; sem `raw()` ou `cursor.execute(f"...")` |
| XSS | Frontend faz render; backend não retorna HTML |
| CSRF | API stateless via JWT (sem cookies de sessão para endpoints API) |
| Brute force login | Throttle DRF + log de tentativas em `audit.ActivityLog` |
| Secrets expostos | Env vars validadas no boot; sem log de tokens/keys |
| Prompt injection | Guardrails determinísticos pré-prompt; system prompt isola instruções de usuário |
| Resource exhaustion (LLM) | `MAX_TOKENS_PER_RESPONSE`, `MAX_MESSAGES_PER_CONVERSATION`, throttle `chat`: 10/min |
| Upload malicioso | Tamanho ≤ 10MB, validação de mimetype; PDFs processados em sandbox de processo (futuro) |
| Vazamento de PII em logs | Filter custom em `LOGGING` que descarta `content` de mensagens |

---

## Observabilidade

- **Request ID:** middleware adiciona `X-Request-ID` (uuid) e propaga em logs
- **Logs estruturados:** JSON formatter com campos `timestamp, level, request_id, user_id, action, latency_ms`
- **Métricas (MVP):** endpoint admin agrega contadores diretamente do banco
- **Métricas (fase 2):** Prometheus + grafana via `django-prometheus`
- **Erros não tratados:** retornados como `INTERNAL_ERROR` com `request_id` no body para correlação

---

## Migração Futura

### ChromaDB → pgvector
1. Habilitar `CREATE EXTENSION vector` no Postgres
2. Trocar `vector_store.py` para usar `langchain_postgres.PGVector`
3. Reindexar documentos (job único)
4. Sem mudança no contrato `retriever.search()`

### Indexação síncrona → Celery
1. Adicionar `redis` e `celery` como dependências
2. Mover `ingestion.ingest()` para task `@shared_task`
3. View do upload chama `task.delay()` e retorna 202 com `KnowledgeDocument.id`
4. Cliente faz polling em `/status` (já contemplado no contrato)

### LLM Provider adicional (Bedrock, Vertex)
1. Implementar `BedrockProvider(LLMProvider)` em `apps/ai_engine/providers/`
2. Adicionar branch em `providers/__init__.py::get_provider()`
3. Sem impacto no orquestrador

### Separar IA em microserviço Python
- Criar `services/ai-service/` com FastAPI expondo `/generate` (HTTP interno)
- Django passa a chamar o serviço via `httpx`
- Mantém contrato externo igual

---

## Ambientes

| Ambiente | Banco | Vector | LLM |
|---|---|---|---|
| **dev (DevContainer)** | Postgres no Compose | Chroma volume local | Provider configurado em `.env` |
| **CI** | Postgres em service | Chroma in-memory | LLM mockado (sem chamadas reais) |
| **prod (single-node)** | Postgres em volume Docker | Chroma volume Docker | OpenAI/Anthropic via API key em secret manager |

---

## Healthcheck

```python
GET /health → 200 OK
{
  "status": "ok",
  "db": "ok",                  # SELECT 1 no Postgres
  "vector_store": "ok",        # collection.count() em Chroma
  "version": "0.1.0",
  "request_id": "..."
}
```

Se algum subsistema falhar, retorna 503 com o sub-status como `"error"` e `error_message` em log.

---

*Próximo documento: [TASKS.md](TASKS.md)*

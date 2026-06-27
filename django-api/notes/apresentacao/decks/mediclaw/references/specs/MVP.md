# MediClaw — Especificação Funcional e Técnica do MVP

> Versão: 1.0 | Data: 2026-05-07 | Status: Rascunho
> **Escopo deste documento:** Backend (Django + DRF). Frontend React é cliente externo.

---

## 1. Visão Geral do Produto

### Posicionamento

MediClaw é um sistema inteligente de apoio à **longevidade e bem-estar funcional**. O backend Django expõe APIs REST que recebem dados biométricos (peso, sono, atividade, alimentação) e oferecem orientações personalizadas via chat com IA, embasadas em literatura científica através de RAG (Retrieval-Augmented Generation).

> O sistema **não realiza diagnóstico médico nem prescrição**. Toda recomendação é educativa e preventiva, e direciona o usuário a procurar um profissional de saúde para decisões clínicas.

### Personas Primárias

| Persona | Descrição | Principal necessidade |
|---|---|---|
| **Usuário Final** | Adulto interessado em longevidade que registra dados biométricos | Interpretação integrada e personalizada dos próprios dados |
| **Administrador** | Gestor da plataforma e da base científica | Curadoria de fontes, monitoramento de uso e qualidade da IA |

### Proposta de Valor

- Interpretação integrada de dados biométricos heterogêneos
- Recomendações personalizadas embasadas em ciência (RAG)
- Disponibilidade 24/7 com custo marginal baixo
- Privacidade dos dados de saúde por design (LGPD Art. 11)

---

## 2. Funcionalidades Principais (MVP — Backend)

### 2.1 Autenticação e Cadastro
- Cadastro de usuário com e-mail, senha e consentimento LGPD
- Login com JWT (access + refresh) via `djangorestframework-simplejwt`
- Endpoint `/me` para perfil
- Atualização de perfil básico (nome, data de nascimento, sexo biológico)

### 2.2 Logs de Saúde (CRUD)
- Registro de peso, sono (horas + qualidade), atividade física (tipo + duração), alimentação livre-texto
- Listagem paginada por usuário e tipo
- Agregações simples (média de sono nos últimos 7 dias, etc.)

### 2.3 Chat com IA
- Criação e listagem de conversas
- Envio de mensagens com resposta da IA via streaming (SSE)
- Histórico persistido com tokens consumidos por mensagem
- Limite de 50 mensagens/conversa para controle de custo

### 2.4 Camada de IA com Guardrails
- Orquestrador que monta prompts a partir de: system prompt + dados de saúde do usuário + RAG + histórico
- **Guardrails** que bloqueiam pedidos de diagnóstico, prescrição e urgência médica
- **Skills** invocáveis pela IA: cálculo de IMC, conversão de unidades, agregação de dados de saúde

### 2.5 RAG sobre Literatura Científica
- Upload e indexação de documentos (PDF/MD/TXT) por admin
- Chunking + embeddings + persistência em ChromaDB
- Recuperação top-K com score mínimo configurável
- Citações de fonte injetadas na resposta da IA

### 2.6 Auditoria e Métricas
- Log de atividades sensíveis (login, upload de KB, mensagens enviadas)
- Métricas internas: uso de tokens, latência LLM, taxa de bloqueios por guardrail
- Endpoint admin para visualização

---

## 3. Arquitetura da Solução

### Visão Geral

```
┌──────────────────────────────────────────────────────┐
│                  Cliente Web (React)                 │
└─────────────────────────┬────────────────────────────┘
                          │ HTTPS REST + SSE
┌─────────────────────────▼────────────────────────────┐
│                Django + DRF (Backend)                │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ accounts │  │ health_logs  │  │ conversations│    │
│  └──────────┘  └──────────────┘  └──────┬───────┘    │
│                                         │            │
│                         ┌───────────────▼──────────┐ │
│                         │       ai_engine          │ │
│                         │ (orchestrator+guardrails │ │
│                         │  + skills)               │ │
│                         └───────────────┬──────────┘ │
│                                         │            │
│                         ┌───────────────▼──────────┐ │
│                         │           rag            │ │
│                         │  (ingestion + retrieval) │ │
│                         └───────────────┬──────────┘ │
└─────────────────────────────────────────┼────────────┘
                                          │
        ┌──────────────────┬──────────────┴──────────────┐
        │                  │                             │
┌───────▼──────┐  ┌────────▼────────┐  ┌────────────────▼─────┐
│  PostgreSQL  │  │  LLM Provider   │  │      ChromaDB        │
│   (dados)    │  │ (OpenAI/Anth.)  │  │   (vector store)     │
└──────────────┘  └─────────────────┘  └──────────────────────┘
```

### Decisões Arquiteturais (resumo)

| Decisão | Escolha | Justificativa |
|---|---|---|
| Framework | Django 5 + DRF | Maturidade, admin pronto, ORM robusto |
| Banco | PostgreSQL 16 | Dados relacionais + path para `pgvector` |
| Auth | JWT (`simplejwt`) | Stateless, refresh token incluído |
| Vector Store | ChromaDB local | Zero infra externa no MVP; substituível |
| LLM | Provider-agnóstico (OpenAI/Anthropic) | Evita lock-in, configurável via env |
| Streaming | SSE | Nativo no browser, simples no Django |
| Orquestração IA | LangChain Python | Ferramentas prontas para RAG e tool calling |

Detalhes completos em [ARCHITECTURE.md](ARCHITECTURE.md).

### Princípio Guia

> Arquitetura mínima para validar o produto. Cada peça (Chroma → pgvector, OpenAI ↔ Anthropic, Django sync → async/Celery) é trocável sem reescrever a aplicação.

---

## 4. Estrutura do Projeto

```
mediclaw/
├── config/
│   ├── settings.py            # Lê .env via python-dotenv, valida campos críticos
│   ├── urls.py                # /api/v1/ + /admin/
│   ├── wsgi.py
│   └── asgi.py                # Necessário para SSE em produção
│
├── apps/
│   ├── common/                # Exceções, paginação, renderer customizado
│   │   ├── exceptions.py
│   │   ├── renderers.py       # { data, error, meta }
│   │   ├── permissions.py
│   │   └── pagination.py
│   │
│   ├── accounts/              # Usuários e autenticação
│   │   ├── models.py          # User custom (AbstractUser) + Profile
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services/auth.py
│   │
│   ├── health_logs/           # Dados biométricos
│   │   ├── models.py          # WeightLog, SleepLog, ActivityLog, NutritionNote
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services/aggregate.py
│   │
│   ├── conversations/         # Chat
│   │   ├── models.py          # Conversation, Message
│   │   ├── serializers.py
│   │   ├── views.py           # Inclui endpoint SSE /stream
│   │   ├── urls.py
│   │   └── services/chat.py
│   │
│   ├── ai_engine/             # Orquestrador, guardrails, skills
│   │   ├── orchestrator.py
│   │   ├── prompts.py
│   │   ├── guardrails.py
│   │   ├── skills/
│   │   │   ├── bmi.py
│   │   │   ├── unit_convert.py
│   │   │   └── health_summary.py
│   │   └── providers/
│   │       ├── base.py
│   │       ├── openai_provider.py
│   │       └── anthropic_provider.py
│   │
│   ├── rag/                   # Pipeline RAG
│   │   ├── models.py          # KnowledgeDocument
│   │   ├── ingestion.py       # Loader + Splitter
│   │   ├── retriever.py       # Chroma + similarity
│   │   ├── views.py           # Upload + status (admin)
│   │   └── urls.py
│   │
│   └── audit/                 # Auditoria
│       ├── models.py          # ActivityLog
│       ├── services/log.py
│       └── views.py           # Métricas e logs (admin)
│
├── knowledge_base/            # Documentos fonte (volume Docker)
├── chroma_data/               # Persistência ChromaDB (volume Docker)
├── tests/                     # pytest
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 5. Fluxos do Usuário

### 5.1 Cadastro e Login

```
Cliente → POST /api/v1/auth/register
  {email, password, name, accept_terms=true}
        ↓
  Validação Zod-like (DRF Serializer)
        ↓
  bcrypt(password) + cria User + Profile + accepted_terms_at=now
        ↓
  Retorna { access, refresh, user }

Cliente → POST /api/v1/auth/login
        ↓
  authenticate() → JWT access (30min) + refresh (1d)
```

### 5.2 Chat com RAG

```
1. POST /api/v1/conversations/{id}/messages  { content: "..." }
2. Salva Message(role=USER)
3. Chama orchestrator.generate(query, user_id, conversation_id)
   ├── guardrail_pre(query) → bloqueia diagnóstico/prescrição (curto-circuito)
   ├── retriever(query) → ChromaDB top-5, score ≥ 0.75
   ├── skills_context(user_id) → IMC, médias 7d, etc.
   ├── monta prompt: system + RAG + skills + histórico (6 msgs) + query
   └── llm_provider.stream(prompt, max_tokens=800)
4. Stream SSE → cliente exibe progressivamente
5. guardrail_post(answer) → injeta disclaimer e citações
6. Salva Message(role=ASSISTANT, tokens_used)
7. Registra ActivityLog
```

### 5.3 Ingestão RAG (admin)

```
POST /api/v1/admin/knowledge/upload  (PDF/MD/TXT, multipart)
        ↓
KnowledgeDocument(status=PROCESSING) criado
        ↓
Job síncrono no MVP (ou Celery na fase 2):
  loader → RecursiveCharacterTextSplitter (chunk=1000, overlap=200)
        ↓
  OpenAIEmbeddings → ChromaDB.add_documents(...)
        ↓
status=INDEXED, chunk_count=N
```

---

## 6. Modelo de Dados (resumido)

> Schema completo em [ARCHITECTURE.md §Schema](ARCHITECTURE.md).

```python
# apps/accounts/models.py
class User(AbstractUser):
    email = EmailField(unique=True)
    role = CharField(choices=[("USER","USER"),("ADMIN","ADMIN")], default="USER")
    accepted_terms_at = DateTimeField(null=True)

class Profile(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    birth_date = DateField(null=True)
    biological_sex = CharField(choices=[("M","M"),("F","F"),("OTHER","OTHER")], null=True)
    height_cm = PositiveSmallIntegerField(null=True)

# apps/health_logs/models.py
class WeightLog(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    value_kg = DecimalField(max_digits=5, decimal_places=2)
    measured_at = DateTimeField()

class SleepLog(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    duration_hours = DecimalField(max_digits=4, decimal_places=2)
    quality_score = PositiveSmallIntegerField()  # 1-10
    started_at = DateTimeField()

class ActivityLog(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    type = CharField(max_length=40)  # walking, running, strength, ...
    duration_min = PositiveSmallIntegerField()
    performed_at = DateTimeField()

class NutritionNote(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    note = TextField()
    logged_at = DateTimeField()

# apps/conversations/models.py
class Conversation(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    title = CharField(max_length=120, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class Message(Model):
    ROLE_CHOICES = [("USER","USER"),("ASSISTANT","ASSISTANT"),("SYSTEM","SYSTEM")]
    conversation = ForeignKey(Conversation, on_delete=CASCADE, related_name="messages")
    role = CharField(max_length=10, choices=ROLE_CHOICES)
    content = TextField()
    tokens_used = PositiveIntegerField(null=True)
    blocked_by_guardrail = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

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

# apps/audit/models.py
class ActivityLog(Model):
    user = ForeignKey(User, on_delete=SET_NULL, null=True)
    action = CharField(max_length=60)
    metadata = JSONField(default=dict)
    created_at = DateTimeField(auto_now_add=True)
```

### Índices críticos

```python
# Em models.py via Meta.indexes
Index(fields=["user", "-measured_at"])     # WeightLog, SleepLog, ActivityLog
Index(fields=["conversation", "created_at"])  # Message
Index(fields=["user", "-updated_at"])      # Conversation
Index(fields=["user", "-created_at"])      # audit.ActivityLog
```

---

## 7. Estratégia de IA e RAG

### Modelos

| Componente | Modelo padrão | Alternativa |
|---|---|---|
| Chat | `gpt-4o-mini` | `claude-haiku-4-5` |
| Embeddings | `text-embedding-3-small` | — |

### Pipeline RAG

```
Indexação (offline, admin):
  PDF/MD/TXT → RecursiveCharacterTextSplitter(chunk=1000, overlap=200)
              → OpenAIEmbeddings → ChromaDB.persist(/app/chroma_data)

Recuperação (online):
  Query → embed → ChromaDB.similarity_search_with_score(k=5)
        → filtra score ≥ 0.75 → contexto
        → prompt template (system + RAG + skills + histórico + query)
        → LLM stream → SSE
```

### System Prompt Base (resumo)

```
Você é o MediClaw, assistente de saúde preventiva e longevidade.

Diretrizes obrigatórias:
- NUNCA dê diagnóstico médico, prescrição ou interpretação clínica de exames.
- Use APENAS o contexto científico fornecido para embasar afirmações técnicas.
- Sempre cite a fonte quando a recomendação vier do contexto.
- Adicione disclaimer: "Esta orientação é educativa e não substitui um profissional de saúde."
- Em caso de sintoma de urgência (dor torácica, falta de ar, etc.), oriente buscar atendimento imediato.

Dados do usuário (skills):
{user_health_summary}

Contexto científico (RAG):
{rag_context}

Histórico recente:
{history}
```

### Guardrails

| Tipo | Implementação |
|---|---|
| **Pré-prompt** | Classificador determinístico (regex + keywords) → bloqueia pedidos explícitos de diagnóstico/prescrição |
| **Prompt-level** | System prompt rígido + few-shot de recusas |
| **Pós-prompt** | Verificação se a resposta contém termos proibidos; se sim, regenera ou bloqueia |
| **Disclaimer** | Injetado automaticamente em qualquer resposta com viés clínico |

### Skills (function calling)

| Skill | Entrada | Saída |
|---|---|---|
| `calculate_bmi` | `weight_kg, height_cm` | BMI + classificação OMS |
| `convert_units` | `value, from_unit, to_unit` | valor convertido |
| `health_summary` | `user_id` | médias 7/30 dias de sono, peso, atividade |

---

## 8. APIs (resumo)

> Lista detalhada com payloads em [PRD.md](PRD.md).

```
# Auth
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
PATCH  /api/v1/auth/me

# Health Logs
GET    /api/v1/health/weight
POST   /api/v1/health/weight
GET    /api/v1/health/sleep
POST   /api/v1/health/sleep
GET    /api/v1/health/activity
POST   /api/v1/health/activity
GET    /api/v1/health/nutrition
POST   /api/v1/health/nutrition
GET    /api/v1/health/summary           # Agregações 7d/30d

# Conversations & Chat
GET    /api/v1/conversations
POST   /api/v1/conversations
GET    /api/v1/conversations/{id}
DELETE /api/v1/conversations/{id}
POST   /api/v1/conversations/{id}/messages
GET    /api/v1/conversations/{id}/stream     # SSE

# RAG (admin)
GET    /api/v1/admin/knowledge
POST   /api/v1/admin/knowledge/upload
GET    /api/v1/admin/knowledge/{id}/status
DELETE /api/v1/admin/knowledge/{id}

# Auditoria & Métricas (admin)
GET    /api/v1/admin/metrics
GET    /api/v1/admin/logs
GET    /health                                # Liveness probe
```

### Streaming SSE

```
GET /api/v1/conversations/{id}/stream
Content-Type: text/event-stream

data: {"type":"token","content":"Considerando"}
data: {"type":"token","content":" seus dados"}
data: {"type":"citation","source":"Sleep Foundation 2024","chunk_id":"abc"}
data: {"type":"done","tokens_used":142,"blocked":false}
```

---

## 9. Segurança e LGPD

### Segurança Técnica

| Camada | Medida |
|---|---|
| Senhas | `make_password` (PBKDF2 padrão Django) |
| JWT | Access 30min + refresh 1d, secret rotacionável |
| Inputs | DRF Serializers com `validators=` explícitos |
| SQL Injection | Django ORM parametrizado (sem `cursor.execute(f"...")`) |
| CORS | `django-cors-headers` com whitelist via env |
| Rate limiting | DRF Throttling (anon 30/min, user 60/min, chat 10/min) |
| Headers | `SECURE_*` settings + `django-csp` (futuro) |
| Logs sensíveis | Sem conteúdo de mensagens; apenas metadados |

### LGPD

| Requisito | Implementação no MVP |
|---|---|
| Consentimento | `accepted_terms_at` obrigatório no cadastro |
| Finalidade | Documentada nos termos vinculados ao cadastro |
| Minimização | Apenas e-mail, nome e dados de saúde voluntariamente registrados |
| Direito ao esquecimento | `DELETE /api/v1/auth/me` → cascade em conversas, mensagens, logs |
| Retenção | `CONVERSATION_RETENTION_DAYS=90`, job de limpeza (Celery beat na fase 2) |
| Disclaimer | Injetado pela camada de IA em toda resposta clínica |

> Dados de saúde são **dados sensíveis** (LGPD Art. 11). Antes do go-live público, requer revisão por DPO e criptografia em repouso (volume PostgreSQL).

---

## 10. Roadmap

### Fase 1 — MVP (0–3 meses)
- [x] Foundation Django + Postgres + Docker
- [ ] Auth JWT
- [ ] CRUD de health logs
- [ ] Chat + AI orchestration + guardrails
- [ ] RAG com ChromaDB
- [ ] Painel admin para KB
- [ ] Suite de testes (incluindo guardrails)

### Fase 2 — Consolidação (3–6 meses)
- [ ] Migração ChromaDB → `pgvector`
- [ ] Tarefas assíncronas com Celery + Redis (indexação, retenção)
- [ ] Exportação de dados (LGPD)
- [ ] Métricas avançadas (latência por modelo, custo por usuário)
- [ ] Recuperação de senha por e-mail

### Fase 3 — Escala (6–12 meses)
- [ ] Microserviço de IA em FastAPI separado
- [ ] Integrações com wearables (Google Fit, Apple Health)
- [ ] Multi-tenancy
- [ ] Notificações in-app

### Fase 4 — Inteligência avançada (12+ meses)
- [ ] Fine-tuning de modelo em literatura de longevidade
- [ ] Agentes autônomos para follow-up
- [ ] Análise de exames laboratoriais com OCR

---

## 11. Backlog Inicial do MVP

### Épicos (mapeados ao Plano-MVP)

| Plano-MVP Etapa | Épico BMAD | Foco |
|---|---|---|
| Etapa 1 | E1 — Foundation | Docker, Django, Postgres, settings, common |
| Etapa 1 | E2 — Auth & Users | User custom, JWT, /me, LGPD consent |
| Etapa 2 | E3 — Core API | Health logs CRUD + agregações + service layer |
| Etapa 3 | E4 — AI Engine | Orchestrator, providers, guardrails, skills |
| Etapa 4 | E5 — RAG | Ingestion, ChromaDB, retriever, admin upload |
| Etapa 6 | E6 — Conversations & Chat | Conversations, messages, SSE streaming, audit |
| Etapa 6 | E7 — Testing & Hardening | pytest, coverage, guardrail eval, deploy |

### MoSCoW

**Must Have (MVP bloqueante):** US-01..US-04, US-06..US-09, US-11..US-15, US-18, US-19, US-21
**Should Have:** US-05, US-10, US-16, US-20
**Could Have:** US-17
**Won't Have (fora do MVP):** wearables, multi-tenancy, e-mail transacional, OCR de exames

> Detalhamento e critérios de aceite em [PRD.md](PRD.md).

---

## Apêndice: Dependências Principais

```txt
# requirements.txt (MVP)
Django==5.2.1
djangorestframework==3.16.0
djangorestframework-simplejwt==5.5.0
psycopg[binary]==3.2.7
python-dotenv==1.1.0
django-cors-headers==4.7.0

# IA / RAG
langchain==0.3.*
langchain-openai==0.3.*
langchain-anthropic==0.3.*
langchain-community==0.3.*
chromadb==0.5.*
openai>=1.30
anthropic>=0.34

# Utilidades
pypdf>=4.0
pydantic>=2.7

# Dev
pre-commit==4.2.0
black==25.1.0
pytest==8.*
pytest-django==4.*
```

---

*Próximo documento: [PRD.md](PRD.md)*

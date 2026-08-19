# Arquitetura de Referência — MediClaw

> Gerado pelo **Arquiteto** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO (extraído do código) | 🟡 INFERIDO | 🔴 LACUNA
> Artefato transversal — síntese arquitetural consolidada dos artefatos de Scout, Arqueólogo e Detetive.

---

## 1. Visão geral

O MediClaw é um **monorepo cliente-servidor** para apoio à longevidade e bem-estar preventivo. Um **médico** conversa com um assistente de IA sobre um paciente em atendimento; a IA registra dados biométricos a partir da linguagem natural e responde com apoio clínico embasado numa base de conhecimento (RAG). **A IA nunca emite diagnóstico definitivo nem prescrição.**

### Componentes de nível superior

| Componente | Tecnologia | Papel | Porta (prod) |
|---|---|---|---|
| **Painel React** | Next.js 16 + React 19 + TypeScript + Chakra UI | SPA consumida pelo médico | `127.0.0.1:3001` |
| **API Django** | Django 5.2 + DRF 3.16 + JWT | Backend REST + streaming SSE | `127.0.0.1:8000` |
| **PostgreSQL** | 16 + extensão `pgvector` | Banco relacional | rede interna Docker |
| **ChromaDB** | 0.5 local (volume) | Vector store do RAG | rede interna Docker |
| **Nginx (host)** | sistema (apt) + Let's Encrypt | Proxy reverso e TLS | 80/443 |

> Topologia de produção (ADR-006): Docker Compose publica **apenas em `127.0.0.1`**; o Nginx do host faz o proxy reverso para o mundo. Vhosts: domínio raiz serve a landing estática, `api.*` proxia para o Django, `painel.*` para o React. 🟢

### Restrições não-negociáveis (invariantes)

| # | Invariante | Aplicação |
|---|---|---|
| I1 | IA nunca diagnostica/prescreve | Guardrails entrada+saída, prompt, disclaimer obrigatório |
| I2 | Chat sempre com o médico | Paciente descrito em terceira pessoa; sem login de paciente |
| I3 | Dados de saúde são sensíveis (LGPD Art. 11) | Consentimento no cadastro, minimização, exclusão em cascata |
| I4 | Logs biométricos são append-only | Sem PATCH/PUT nos ViewSets de logs |
| I5 | Ownership rígido por médico | Querysets filtram `doctor=request.user`; recurso alheio → 404 |
| I6 | Resposta clínica termina com disclaimer | Anexado pelo orquestrador se ausente |

---

## 2. Estilos e decisões arquiteturais

### 2.1 Monorepo com três camadas independentes

```
mediclaw/
├── django-api/    # Backend (Python 3.12, uv)
├── react-painel/  # Frontend (Next.js, npm)
├── marketing/     # Landing estática (HTML/CSS)
├── nginx/         # Configs de proxy/TLS do host
└── docker-compose.prod.yml  # Stack de produção
```

Backend e frontend são **deployáveis e evoluíveis de forma independente**, comunicando-se apenas via HTTP (REST + SSE). Não há SSR para dados do painel: o React consome a API com `NEXT_PUBLIC_API_URL`. 🟢

### 2.2 Backend: Django por domínio com service layer

- **8 apps Django** (`accounts`, `patients`, `health_logs`, `conversations`, `ai_engine`, `rag`, `audit`, `common`), um domínio por app.
- **Camada de serviços**: lógica de negócio em `apps/<app>/services/` (ex.: `patients/services/patient.py`, `health_logs/services/persist.py`). Views orquestram HTTP.
- **`common` como infraestrutura transversal**: renderer de envelope, exception handler, permissions, paginação, middlewares e structlog. 🟢
- **Rotas centralizadas**: `config/urls.py` monta `/api/v1/` por namespace de app; `audit/urls.py` funciona como hub de rotas admin (criação de usuário e métricas).

### 2.3 Padrão de resposta da API (envelope)

Toda resposta DRF passa pelo `EnvelopeJSONRenderer` → `{data, error, meta}`. Erros passam pelo `envelope_exception_handler` com código `SNAKE_CASE` (ex.: `INVALID_CREDENTIALS`, `GUARDRAIL_BLOCKED`, `LLM_PROVIDER_ERROR`). 🟢

> **Exceção de padrão:** pacientes e conversas usam **paginação manual** (`{results, count, next}` via slicing) em vez do `DefaultPagination` global; serialização manual via helpers `_serialize_*` em vez de serializers. Registrar como dívida de consistência. 🟡

### 2.4 Autenticação JWT no cliente (ADR-002)

- Access (30 min) + refresh (1 dia) retornados no corpo do login/register; `Authorization: Bearer` no header.
- **Streaming SSE** usa `?token=<AccessToken>` no query string (EventSource não envia headers). 🟡 vaza em logs de proxy.
- Retirada a migração para cookies HttpOnly (revert `3ca2a7d`/`004e4e2`); razão exata não documentada. 🟡

### 2.5 Orquestração de IA com camada dupla de segurança (ADR-003)

Fluxo de uma mensagem (REST/SSE):

```
check_input (urgency→diagnosis→prescription→gibberish)
  → [se bloqueado] canned_reply + DISCLAIMER, blocked=True
  → capture_from_message (regex → LLM opcional → persiste Patient/logs)
  → _resolve_messages (escolhe modo: normal | focus | soft)
  → get_provider (OpenAI | Gemini)
  → provider.complete / provider.stream
  → check_output (forbidden_output)
  → garante DISCLAIMER → resposta + citações RAG
```

- **Guardrails determinísticos** por regex (ADR-003) — sem custo de LLM em bloqueios de entrada.
- **Onboarding focus/soft** (ADR-008): perfil incompleto + primeira mensagem → só orienta o registro; depois → responde com lembrete.
- **Captura rules-first** (ADR-004): regex têm precedência; LLM opcional (`DATA_CAPTURE_LLM`) só preenche lacunas.
- **RAG** (ADR-005): ChromaDB local, collection `mediclaw_kb`, `space='l2'`, score `max(0, 1 − dist/2)`, `RAG_TOP_K=5`, `RAG_MIN_SCORE=0.75` (env) injetados pelo orquestrador.

---

## 3. Camadas e componentes

### 3.1 Componentes do backend (por app)

| App | Responsabilidade | Consome | É consumido por |
|---|---|---|---|
| `accounts` | User custom, JWT, perfil, admin users | `common`, `conversations` (welcome), `audit` | `common`, todos (auth global) |
| `patients` | CRUD de pacientes + dedup no chat | `health_logs` (WeightLog), `conversations`, `common` | `ai_engine`, `health_logs`, frontend |
| `health_logs` | Logs biométricos + resumo agregado | `patients`, `common` | REST (frontend), `ai_engine` (persist + summarize) |
| `conversations` | Chat REST + streaming SSE | `ai_engine` (orquestrador), `common` | `accounts` (welcome), `patients`, `rag` (métricas), frontend |
| `ai_engine` | Orquestrador, guardrails, captura, skills, providers | `rag` (retriever), `health_logs` (persist/summarize), `patients`, `conversations`, `audit`, `common` | `conversations` (indireto) |
| `rag` | KB: ingestão, ChromaDB, retrieval, admin | `accounts`, `conversations` (métricas), `audit`, `common` | `ai_engine` (retriever), frontend (admin) |
| `audit` | `record()` (stub) + hub de rotas admin | — (stub) | `accounts`, `rag`, `ai_engine` (chamam `record`) |
| `common` | Infra: envelope, exceptions, permissions, middleware, logging, health | `rag` (Chroma health), `django.db` | **Todos** |

> Detalhamento por app em `code-analysis.md`; relacionamentos entre containers e componentes em `c4-containers.md` e `c4-components.md`.

### 3.2 Componentes do frontend

| Área | Componentes | Função |
|---|---|---|
| Auth | `AuthContext`, `lib/auth.ts`, interceptor Axios | Gestão de tokens, refresh automático, proteção de rotas |
| Chat | rotas `/chat`, `/chat/[id]` | Conversa com a IA via **EventSource** (`/stream/`) |
| Pacientes | rotas `/patients`, `/patients/[id]` | Lista/detalhe com tabs de saúde |
| Admin | `/admin/metrics`, `/conhecimento` | Métricas do dia + KB (upload/list) |
| Design | Chakra UI 3 + Emotion | Design system de componentes |

### 3.3 Integrações externas

| Integração | Protocolo | Uso | Direção |
|---|---|---|---|
| **OpenAI API** | HTTPS | Chat `gpt-4o-mini` + embeddings `text-embedding-3-small` (1536 dim) | Saída |
| **Google Gemini API** | HTTPS | Chat `gemini-2.0-flash` (alternativa via `LLM_PROVIDER`) | Saída |
| **PostgreSQL 16** | TCP 5432 (rede interna) | Banco relacional + `pgvector` (extensão; vector store futuro) | Saída |
| **ChromaDB** | processo local (volume `chroma_data`) | Vector store do RAG (collection `mediclaw_kb`) | Local |
| **Nginx + Let's Encrypt** | HTTPS/HTTP | TLS e proxy reverso no host | Infra |

> **Divergência de spec (🟡):** PROJECT-CONTEXT.md prevê `LLM_PROVIDER = openai | anthropic`, mas o código implementa **OpenAI + Google Gemini**. O provider Anthropic não existe. Consumidores: `apps/ai_engine/providers/`.

---

## 4. Fluxos principais

### 4.1 Cadastro (register)

`POST /auth/register/` → valida (senha, termos LGPD, email único) → `create_user` (`accepted_terms_at=now`) → gera tokens → `record("USER_REGISTERED")` → cria conversa "Bem-vindo" (idempotente; pulada p/ `ADMIN`) → 201.

### 4.2 Turno de chat com captura (stream)

`GET /conversations/<id>/stream/?token=&prompt=` → valida token/prompt/limite → persiste mensagem USER (transaction.atomic) → seta título (`prompt[:80]`) → `orchestrator.generate_stream`: guardrail de entrada → captura de dados (persiste `Patient`/logs) → monta prompt (histórico 6 + resumo de saúde + RAG top-5) → provider.stream → eventos `citation`/`token`/`done` → check_output → salva ASSISTANT com metadados.

### 4.3 RAG (upload e retrieval)

**Upload:** `POST /admin/knowledge/upload/` → valida mime/tamanho → `KnowledgeDocument(PROCESSING)` → `ingest()` **síncrono** (extrai texto → chunk 1000/200 → embeddings → grava Chroma) → `INDEXED`/`ERROR`. **Retrieval:** `search(query, k=5, min_score=0.75)` → embed_query → query Chroma → converte distância L² em cosseno → filtra score → chunks com `source`/`chunk_id`.

---

## 5. Dívidas técnicas e riscos

Consolidado de `code-analysis.md`, `permissions.md` e `state-machines.md`:

### 5.1 Segurança e conformidade

| # | Dívida | Severidade | Confiança |
|---|---|---|---|
| D1 | **Retenção LGPD de 90 dias não implementada** — sem job de expurgo; soft-delete sem purga; dados acumulam indefinidamente | 🔴 crítica | 🟢 |
| D2 | **`ActivityLog` de auditoria não existe** — `record()` é stub `pass`; eventos descartados (Epic 3) | 🔴 alta | 🟢 |
| D3 | **KB aberta a qualquer autenticado** — rotas sob `/api/v1/admin/` mas só `metrics` exige `IsAdminRole`; vetor de content poisoning do chat | 🟠 alta | 🟡 |
| D4 | **Stream sem throttle** — caminho principal do frontend não tem `ChatThrottle` (10/min) | 🟠 média | 🟢 |
| D5 | **Token no query string do stream** — vaza em access log do Nginx | 🟠 média | 🟡 |
| D6 | **Swagger/Redoc públicos** (`AllowAny`) em produção | 🟡 média | 🟢 |

### 5.2 Correção e consistência

| # | Dívida | Severidade | Confiança |
|---|---|---|---|
| D7 | **Código de erro divergente** — `CONVERSATION_FULL` no código vs `CONVERSATION_LIMIT_REACHED` na spec | 🟠 média | 🟢 |
| D8 | **`MAX_MESSAGES` hardcoded `50`** em views vs env `MAX_MESSAGES_PER_CONVERSATION` no service | 🟠 média | 🟢 |
| D9 | **Validações duplicadas e divergentes** entre REST (serializers) e chat (services.persist) — ex.: faixa de sono, nota mínima | 🟡 baixa | 🟢 |
| D10 | **`except (…, Exception)` catch-all** no stream e no `data_extraction_llm` mascaram erros de programação | 🟠 média | 🟢 |
| D11 | **`patient_created` sempre `False`** — atributo `_patient_just_created` nunca é definido | 🟡 baixa | 🟡 |
| D12 | **`tokens_used` no streaming conta palavras**, não tokens (métrica diverge do REST) | 🟡 baixa | 🟡 |

### 5.3 Qualidade e padrões

| # | Dívida | Severidade | Confiança |
|---|---|---|---|
| D13 | **Paginação/serialização manual** em patients e conversations vs padrão global do DRF | 🟡 baixa | 🟢 |
| D14 | **Código morto:** `IsOwner` e `GuardrailBlockedError` definidos mas nunca usados | 🟡 baixa | 🟢 |
| D15 | **`os.getenv` fora de `settings.py`** no `ai_engine` (orquestrador, providers, data_extraction_llm) — fere convenção | 🟡 baixa | 🟢 |
| D16 | **Ingestão síncrona no request** — upload de até 10 MB trava a requisição; sem fila/background | 🟡 média | 🟢 |
| D17 | **Sem re-tentativa de documento `ERROR`** no RAG — correção só por re-upload | 🟡 baixa | 🟢 |
| D18 | **Sem promoção de role via API** — admin depende de acesso manual | 🟡 baixa | 🟢 |
| D19 | **`tokens_used`/latência/auditoria** sem persistência estruturada (mitigado por `Message.metadata`) | 🟡 média | 🟢 |

---

## 6. Migração futura prevista

| Item | Previsão | Evidência |
|---|---|---|
| `pgvector` para vector store (substituir Chroma local) | Epic 9 (pós-MVP) | ADR-005, commit `0d6a52d` 🟢 |
| Auditoria persistida (`ActivityLog`) | Epic 3 | ADR-007 🟢 |
| Multi-tenancy | Epic 9 (pós-MVP) | commit `0d6a52d` 🟢 |
| Provider Anthropic | documentado na spec, ausente no código | PROJECT-CONTEXT.md 🟡 |

---

## 7. Artefatos relacionados

| Artefato | Conteúdo |
|---|---|
| `c4-context.md` | Diagrama C4 Nível 1 (sistema + atores + externos) |
| `c4-containers.md` | Diagrama C4 Nível 2 (aplicações, banco, vector store) |
| `c4-components.md` | Diagrama C4 Nível 3 (apps Django + frontend) |
| `erd-complete.md` | ERD com cardinalidades, PKs e FKs |
| `traceability/spec-impact-matrix.md` | Matriz de impacto entre componentes |
| `code-analysis.md`, `data-dictionary.md`, `domain.md`, `state-machines.md`, `permissions.md`, ADRs | Base de extração |

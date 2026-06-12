# MediClaw — Product Requirements Document (PRD)

> **Versão:** 1.0 | **Data:** 2026-05-07 | **Status:** Aprovado
> **Referência:** [MVP.md](MVP.md) | **Próximo:** [ARCHITECTURE.md](ARCHITECTURE.md) → [TASKS.md](TASKS.md)
> **Escopo:** Backend (Django + DRF). Frontend é cliente externo.

---

## Objetivo do Produto

Construir um backend Django que sirva uma plataforma de apoio à longevidade e saúde preventiva. O sistema recebe dados biométricos do usuário e fornece, via chat, recomendações personalizadas geradas por LLM com embasamento em literatura científica (RAG) e protegidas por guardrails contra diagnóstico/prescrição.

**Restrição central:** O sistema **NÃO** realiza diagnóstico médico nem prescrição. Toda resposta é educativa.

---

## Personas

### P1 — Usuário Final (Marina, 38 anos)
- Pratica atividade física regular e quer otimizar longevidade
- Registra peso, sono e refeições semanalmente
- Quer entender padrões nos próprios dados sem precisar consultar um médico para cada dúvida
- Conhecimento técnico: básico/médio

### P2 — Administrador
- Profissional de saúde ou engenheiro responsável pela plataforma
- Mantém a base de conhecimento científica curada
- Monitora qualidade da IA (taxa de bloqueio, latência, custo)

### P3 — Sistema de IA (persona técnica)
- O orquestrador atua como persona implícita no system prompt
- Sempre responde em português, com tom acessível e baseado em ciência

---

## Métricas de Sucesso do MVP

| Métrica | Meta (90 dias) |
|---|---|
| Usuários cadastrados | ≥ 100 |
| Sessões de chat por usuário/semana | ≥ 1,5 |
| Custo médio LLM por conversa | < R$ 0,15 |
| Tempo até primeiro token (p95) | < 1,8s |
| Taxa de bloqueios indevidos pelo guardrail | < 5% (falsos positivos em testes) |
| Taxa de detecção de diagnóstico (true positive) | ≥ 95% no conjunto de avaliação |
| Cobertura de testes (linhas) | ≥ 80% nos apps `accounts`, `health_logs`, `ai_engine` |

---

## Requisitos Não-Funcionais

### RNF-01 — Segurança
- Senhas via `make_password` (PBKDF2 default do Django, ≥ 600k iterações na 5.x)
- JWT com `ACCESS_TOKEN_LIFETIME=30min`, `REFRESH_TOKEN_LIFETIME=1 day`
- Validação de inputs em DRF Serializers (sempre)
- Rate limiting via DRF Throttling: anon 30/min, user 60/min, chat 10/min
- CORS restrito via env `CORS_ALLOWED_ORIGINS`
- Sem `cursor.execute(f"...")` ou raw SQL não parametrizado

### RNF-02 — LGPD
- Consentimento explícito no cadastro (`accept_terms=true` obrigatório, persistido em `accepted_terms_at`)
- Dados mínimos: e-mail, nome, perfil opcional + logs voluntários
- Cascade delete na exclusão de conta
- Retenção de conversas: 90 dias (env)
- Dados de saúde tratados como sensíveis (Art. 11 LGPD)
- Sem log de conteúdo de mensagens em produção

### RNF-03 — Performance
- Tempo até primeiro token (TTFT) p95 < 1,8s
- Listagem de logs e conversas: p95 < 400ms
- Indexação RAG: síncrona no MVP (admin aceita esperar até ~30s/doc); async em fase 2
- Suporte a 30 usuários simultâneos no MVP single-node

### RNF-04 — Custo de IA
- Modelo padrão `gpt-4o-mini` (configurável via env)
- Limite de 800 tokens por resposta
- Limite de 50 mensagens por conversa
- Histórico no prompt limitado às últimas 6 mensagens

### RNF-05 — Infraestrutura
- DevContainer e Docker Compose já presentes
- Volume Docker para Postgres e ChromaDB
- Healthcheck `GET /health` retornando `{"status":"ok","db":"ok","vector_store":"ok"}`
- ASGI server para produção (uvicorn) — necessário para SSE estável

### RNF-06 — Observabilidade
- Logging estruturado (JSON) no nível INFO/WARN/ERROR
- Métricas internas em endpoint admin (sem stack Prometheus no MVP)
- `ActivityLog` para ações sensíveis

---

## Épicos e User Stories

---

### EPIC-01 — Foundation (Etapa 1 do Plano)

**Objetivo:** Estabelecer base do projeto Django: settings, banco, common utils, healthcheck.

#### US-01 — Bootstrap do projeto Django

**Como** desenvolvedor,
**Quero** ter o projeto Django configurado com Postgres, env vars e DRF,
**Para que** o desenvolvimento dos apps possa iniciar.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E1](epics/epic-1-foundation.md)

**Critérios de Aceite:**
- [ ] `python manage.py runserver` sobe sem warnings críticos
- [ ] `python manage.py migrate` aplica migrations com sucesso no Postgres
- [ ] `config/settings.py` lê todas as envs via `os.environ` validado em tempo de boot (falha rápido se falta)
- [ ] DRF instalado com renderer customizado `{ data, error, meta }` aplicado por padrão
- [ ] App `apps.common` com `exceptions.py`, `renderers.py`, `pagination.py`, `permissions.py`
- [ ] `GET /health` retorna 200 e checa conectividade com Postgres
- [ ] `pre-commit run --all-files` passa (black + isort + flake8 mínimo)

---

#### US-02 — Configuração de logging estruturado

**Como** operador,
**Quero** logs JSON com `request_id` e nível padronizado,
**Para que** eu consiga investigar incidentes em produção.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E1](epics/epic-1-foundation.md)

**Critérios de Aceite:**
- [ ] `LOGGING` configurado em `settings.py` com formatter JSON
- [ ] Middleware injeta `request_id` (uuid) em cada requisição
- [ ] Loggers `django.request`, `apps.*` registrando WARN/ERROR para stderr
- [ ] Sem dados sensíveis em logs (senhas, tokens, mensagens de chat)

---

### EPIC-02 — Auth & Users (Etapa 1 do Plano)

**Objetivo:** Autenticação JWT completa com modelo de usuário customizado e consentimento LGPD.

#### US-03 — Cadastro de usuário

**Como** visitante,
**Quero** me cadastrar com e-mail, senha, nome e aceite dos termos,
**Para que** eu acesse a plataforma.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**
- [ ] `POST /api/v1/auth/register` com `{email, password, name, accept_terms}` cria User + Profile e retorna `{access, refresh, user}`
- [ ] E-mail duplicado → HTTP 400 `EMAIL_ALREADY_EXISTS`
- [ ] `password` com < 8 chars ou sem dígito/letra → HTTP 400 `VALIDATION_ERROR` com `details`
- [ ] `accept_terms != true` → HTTP 400 `VALIDATION_ERROR` (LGPD bloqueante)
- [ ] Senha persistida via `make_password` — nunca em texto puro
- [ ] `accepted_terms_at` populado com `now()`
- [ ] Ação registrada em `audit.ActivityLog` com `action="USER_REGISTERED"`

---

#### US-04 — Login com JWT

**Como** usuário cadastrado,
**Quero** fazer login e receber tokens JWT,
**Para que** eu acesse rotas privadas.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**
- [ ] `POST /api/v1/auth/login` com `{email, password}` retorna `{access, refresh, user}`
- [ ] Credenciais inválidas → HTTP 401 `INVALID_CREDENTIALS` (mensagem genérica, não revela campo)
- [ ] Usuário com `is_active=False` → HTTP 401 `INVALID_CREDENTIALS` (não revela motivo)
- [ ] `POST /api/v1/auth/refresh` aceita refresh válido e retorna novo access
- [ ] Refresh expirado → HTTP 401 `TOKEN_EXPIRED`
- [ ] `LOGIN` registrado em `audit.ActivityLog`

---

#### US-05 — Endpoint /me e atualização de perfil

**Como** usuário logado,
**Quero** consultar e atualizar meu perfil,
**Para que** os dados estejam corretos para personalização da IA.

**Prioridade:** Should | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**
- [ ] `GET /api/v1/auth/me` retorna `{id, email, name, role, profile}` (sem `password`)
- [ ] `PATCH /api/v1/auth/me` permite atualizar `name`, `birth_date`, `biological_sex`, `height_cm`
- [ ] Campos imutáveis (email, role) → HTTP 400 se enviados
- [ ] Sem token → HTTP 401 `MISSING_TOKEN`
- [ ] Token inválido/expirado → HTTP 401 `INVALID_TOKEN` ou `TOKEN_EXPIRED`

---

#### US-06 — Permissões e middleware

**Como** desenvolvedor,
**Quero** que todas as rotas privadas verifiquem JWT automaticamente e que rotas admin verifiquem role,
**Para que** não haja vazamento entre usuários.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**
- [ ] `DEFAULT_PERMISSION_CLASSES = ["IsAuthenticated"]` no DRF
- [ ] `IsAdminRole` permission custom que checa `user.role == "ADMIN"`
- [ ] Token ausente → 401 `MISSING_TOKEN`
- [ ] Token inválido → 401 `INVALID_TOKEN`
- [ ] Role insuficiente → 403 `FORBIDDEN`
- [ ] Acesso a recurso de outro usuário (ex.: conversa de terceiro) → 403 `FORBIDDEN`

---

### EPIC-03 — Core API: Health Logs (Etapa 2 do Plano)

**Objetivo:** Persistir e consultar dados biométricos com agregações usadas pela camada de IA.

#### US-07 — CRUD de logs biométricos

**Como** usuário logado,
**Quero** registrar e listar peso, sono, atividade física e notas de alimentação,
**Para que** a IA tenha dados meus para personalizar respostas.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E3](epics/epic-3-core-api.md)

**Critérios de Aceite:**
- [ ] `POST/GET /api/v1/health/weight` aceita/retorna `{value_kg, measured_at}` com paginação por padrão
- [ ] `POST/GET /api/v1/health/sleep` aceita/retorna `{duration_hours, quality_score(1-10), started_at}`
- [ ] `POST/GET /api/v1/health/activity` aceita/retorna `{type, duration_min, performed_at}`
- [ ] `POST/GET /api/v1/health/nutrition` aceita/retorna `{note, logged_at}` (texto livre, máx 1000 chars)
- [ ] Validações: `value_kg` entre 20 e 400; `quality_score` 1–10; `duration_min` ≥ 1; `measured_at` não pode ser no futuro
- [ ] `DELETE /api/v1/health/<resource>/<id>` apaga apenas registros do próprio usuário; outros → 403
- [ ] Filtros via query: `?from=YYYY-MM-DD&to=YYYY-MM-DD`
- [ ] Listagem ordenada por `measured_at|started_at|performed_at|logged_at` desc

---

#### US-08 — Agregação de saúde

**Como** sistema,
**Quero** obter um sumário consolidado dos logs do usuário,
**Para que** o orquestrador injete contexto na IA.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E3](epics/epic-3-core-api.md)

**Critérios de Aceite:**
- [ ] `GET /api/v1/health/summary?window=7|30` retorna `{avg_sleep_hours, avg_quality, latest_weight, weight_trend, total_activity_min, last_nutrition_notes:[3]}`
- [ ] Valores ausentes retornam `null` (não erro)
- [ ] Apenas dados do usuário autenticado
- [ ] A função `services/aggregate.py::summarize(user_id, window)` é importável pelo `ai_engine`
- [ ] Cobertura de testes ≥ 90% no service

---

### EPIC-04 — AI Engine & Guardrails (Etapa 3 do Plano)

**Objetivo:** Orquestrar respostas da IA com prompts estruturados, guardrails e skills.

#### US-09 — Provider-agnóstico de LLM

**Como** sistema,
**Quero** poder trocar entre OpenAI e Anthropic via env,
**Para que** não haja lock-in e seja possível avaliar custo/qualidade.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E4](epics/epic-4-ai-engine.md)

**Critérios de Aceite:**
- [ ] `apps/ai_engine/providers/base.py` define interface `LLMProvider.stream(messages, max_tokens) → Iterator[str]`
- [ ] `OpenAIProvider` e `AnthropicProvider` implementam a interface
- [ ] `LLM_PROVIDER` em `.env` seleciona o ativo no boot
- [ ] Erro upstream do provedor → exception `LLMProviderError` mapeada para HTTP 502 `LLM_PROVIDER_ERROR`
- [ ] Testes unitários com mock do SDK (sem chamada real)

---

#### US-10 — Orquestrador de prompts

**Como** sistema,
**Quero** montar prompts consistentes combinando system prompt, RAG, skills, histórico e query,
**Para que** as respostas sejam relevantes e seguras.

**Prioridade:** Must | **Esforço:** L | **Epic:** [E4](epics/epic-4-ai-engine.md)

**Critérios de Aceite:**
- [ ] `orchestrator.generate(user_id, conversation_id, query) → Stream` orquestra: guardrail_pre → retriever → skills → prompt → llm → guardrail_post
- [ ] System prompt em `apps/ai_engine/prompts.py` carregado no boot
- [ ] Histórico injetado limitado a `HISTORY_WINDOW=6` últimas mensagens
- [ ] Score < `RAG_MIN_SCORE` → contexto vazio + nota "sem evidências específicas" no prompt
- [ ] Resposta final sempre acompanhada de disclaimer

---

#### US-11 — Guardrails determinísticos

**Como** sistema,
**Quero** bloquear pedidos de diagnóstico, prescrição e urgência médica antes de chegar ao LLM,
**Para que** o produto esteja em conformidade ética e legal.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E4](epics/epic-4-ai-engine.md)

**Critérios de Aceite:**
- [ ] `guardrails.check_input(query) → GuardrailResult{ allowed, reason }` com regras por keyword/regex (ex.: "qual o diagnóstico", "prescreva", "que remédio tomar", "tô passando mal agora")
- [ ] Query bloqueada → HTTP 200 com mensagem educativa pré-definida (não chama LLM); `Message.blocked_by_guardrail=True`
- [ ] `guardrails.check_output(response)` valida que a resposta NÃO contém afirmações tipo "você tem X" / "tome Y"
- [ ] Suíte de testes com ≥ 30 prompts adversariais; ≥ 95% detectados; falsos positivos ≤ 5%
- [ ] Lista de keywords/regex documentada em `apps/ai_engine/guardrails.py`

---

#### US-12 — Skills (function calling)

**Como** sistema,
**Quero** que a IA calcule IMC e converta unidades sob demanda,
**Para que** as respostas sejam precisas em cálculos.

**Prioridade:** Should | **Esforço:** M | **Epic:** [E4](epics/epic-4-ai-engine.md)

**Critérios de Aceite:**
- [ ] Skills registradas em `apps/ai_engine/skills/__init__.py` com schema JSON
- [ ] `calculate_bmi(weight_kg, height_cm)` retorna `{bmi, category}` com classificação OMS
- [ ] `convert_units(value, from_unit, to_unit)` suporta kg↔lb, cm↔in, ml↔fl_oz
- [ ] `health_summary(user_id)` é injetado automaticamente no prompt (não exposto ao tool calling)
- [ ] Testes unitários com casos limite (altura 0, valores negativos → erro)

---

### EPIC-05 — RAG (Etapa 4 do Plano)

**Objetivo:** Recuperação semântica em literatura científica com ingestão administrável.

#### US-13 — Setup do vector store

**Como** sistema,
**Quero** ChromaDB persistido em volume com cliente singleton,
**Para que** a recuperação esteja disponível em qualquer requisição.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E5](epics/epic-5-rag.md)

**Critérios de Aceite:**
- [ ] `apps/rag/vector_store.py` expõe `get_collection()` singleton apontando para `CHROMA_PERSIST_DIR`
- [ ] Coleção criada se não existir; carregada se existir
- [ ] `GET /health` inclui `"vector_store":"ok"` quando coleção responde a `count()`
- [ ] Erro de inicialização registra log ERROR mas não derruba o boot

---

#### US-14 — Pipeline de ingestão

**Como** administrador,
**Quero** carregar PDFs/MDs/TXTs e tê-los indexados automaticamente,
**Para que** a IA cite fontes na resposta.

**Prioridade:** Must | **Esforço:** L | **Epic:** [E5](epics/epic-5-rag.md)

**Critérios de Aceite:**
- [ ] `POST /api/v1/admin/knowledge/upload` (multipart) aceita PDF, MD, TXT, máx 10MB
- [ ] Tipo inválido → HTTP 400 `INVALID_FILE_TYPE`; tamanho excedido → 400 `FILE_TOO_LARGE`
- [ ] `KnowledgeDocument(status=PROCESSING)` criado; chunks gerados via `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`
- [ ] Embeddings via `text-embedding-3-small` adicionados ao Chroma com metadados `{document_id, title, chunk_index}`
- [ ] Sucesso → `status=INDEXED`, `chunk_count=N`; falha → `status=ERROR` com `error_message`
- [ ] No MVP a indexação é síncrona (timeout 60s); fase 2 → Celery
- [ ] Apenas role ADMIN; outros → 403

---

#### US-15 — Recuperação contextualizada

**Como** sistema,
**Quero** buscar chunks relevantes por similaridade,
**Para que** o orquestrador embase a resposta.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E5](epics/epic-5-rag.md)

**Critérios de Aceite:**
- [ ] `retriever.search(query, k=5, min_score=0.75) → list[Chunk{content, source, score}]`
- [ ] Embedding da query usa o mesmo modelo da indexação
- [ ] Filtra chunks com score < 0.75
- [ ] Resposta da IA inclui citação `(fonte: <title>)` quando o chunk foi usado
- [ ] Quando não há chunks relevantes, IA responde genericamente sem inventar fontes

---

#### US-16 — Gestão de documentos

**Como** administrador,
**Quero** listar e remover documentos,
**Para que** eu mantenha a base atualizada.

**Prioridade:** Should | **Esforço:** M | **Epic:** [E5](epics/epic-5-rag.md)

**Critérios de Aceite:**
- [ ] `GET /api/v1/admin/knowledge` lista `{id, title, status, chunk_count, created_at}` paginado
- [ ] `GET /api/v1/admin/knowledge/{id}/status` retorna status atual (polling)
- [ ] `DELETE /api/v1/admin/knowledge/{id}` remove o registro e os chunks correspondentes do Chroma (filtro por `document_id` no metadata)
- [ ] Documento em `PROCESSING` → DELETE retorna HTTP 409
- [ ] Apenas ADMIN; outros → 403

---

### EPIC-06 — Conversations & Chat

**Objetivo:** Implementar conversas persistidas com chat em streaming.

#### US-17 — CRUD de conversas

**Como** usuário logado,
**Quero** criar, listar, ver e deletar conversas,
**Para que** eu controle meu histórico.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E6](epics/epic-6-chat.md)

**Critérios de Aceite:**
- [ ] `POST /api/v1/conversations` cria conversa, retorna `{id, title, created_at}`
- [ ] `GET /api/v1/conversations` lista conversas do usuário ordenadas por `updated_at desc`
- [ ] `GET /api/v1/conversations/{id}` retorna conversa + mensagens paginadas (50/página)
- [ ] `DELETE /api/v1/conversations/{id}` cascade nas mensagens, retorna 204
- [ ] Conversa de outro usuário → 403 `FORBIDDEN`

---

#### US-18 — Envio de mensagem

**Como** usuário no chat,
**Quero** enviar uma mensagem e ter a resposta da IA persistida,
**Para que** eu receba orientação contextualizada.

**Prioridade:** Must | **Esforço:** L | **Epic:** [E6](epics/epic-6-chat.md)

**Critérios de Aceite:**
- [ ] `POST /api/v1/conversations/{id}/messages` com `{content}`:
  - salva `Message(role=USER)`
  - chama orquestrador (não-streaming síncrono nesta rota; streaming é via `/stream`)
  - salva `Message(role=ASSISTANT)` com `tokens_used` e citações em `metadata`
  - retorna a mensagem do assistente
- [ ] `content` vazio ou > 4000 chars → 400 `VALIDATION_ERROR`
- [ ] Conversa com 50 mensagens → 400 `CONVERSATION_LIMIT_REACHED`
- [ ] Bloqueio por guardrail → resposta contém mensagem educativa + `blocked_by_guardrail=true`
- [ ] Erro do provedor LLM → 502 `LLM_PROVIDER_ERROR`; mensagem do usuário permanece salva, mensagem da IA não é criada

---

#### US-19 — Streaming SSE

**Como** usuário,
**Quero** ver a resposta chegando token a token,
**Para que** a experiência seja fluida.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E6](epics/epic-6-chat.md)

**Critérios de Aceite:**
- [ ] `GET /api/v1/conversations/{id}/stream?prompt=...` autentica via JWT (header ou query `?token=` para suporte a EventSource)
- [ ] Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- [ ] Cada token: `data: {"type":"token","content":"..."}\n\n`
- [ ] Citações: `data: {"type":"citation","source":"...","chunk_id":"..."}\n\n`
- [ ] Final: `data: {"type":"done","tokens_used":N,"blocked":false}\n\n` + close
- [ ] Erro: `data: {"type":"error","code":"...","message":"..."}\n\n` + close
- [ ] Mensagem do assistente é persistida ao final (mesmo se cliente desconectar antes)
- [ ] Servir via ASGI (uvicorn) — WSGI/runserver não bloqueia, mas docs alertam para prod ASGI

---

### EPIC-07 — Auditoria, Métricas e Hardening (Etapa 6 do Plano)

**Objetivo:** Observabilidade, testes de IA e checklist de prontidão.

#### US-20 — ActivityLog e métricas

**Como** administrador,
**Quero** ver o que está acontecendo na plataforma,
**Para que** eu detecte abusos e custos anormais.

**Prioridade:** Should | **Esforço:** M | **Epic:** [E7](epics/epic-7-testing.md)

**Critérios de Aceite:**
- [ ] `audit.ActivityLog` registra: `USER_REGISTERED`, `LOGIN`, `MESSAGE_SENT`, `GUARDRAIL_BLOCKED`, `KB_UPLOAD`, `KB_DELETE`
- [ ] `GET /api/v1/admin/logs?user_id=&action=&from=&to=` paginado
- [ ] `GET /api/v1/admin/metrics` retorna `{users_total, conversations_total, messages_today, tokens_today, guardrail_blocks_today, kb_documents_indexed}`
- [ ] Sem cache no MVP (response < 500ms direto do banco)
- [ ] Apenas ADMIN

---

#### US-21 — Suíte de testes e avaliação da IA

**Como** equipe técnica,
**Queremos** uma suíte que cubra fluxos críticos e a qualidade dos guardrails,
**Para que** o MVP seja entregue com confiança.

**Prioridade:** Must | **Esforço:** L | **Epic:** [E7](epics/epic-7-testing.md)

**Critérios de Aceite:**
- [ ] `pytest` configurado com `pytest-django`; banco de teste real (Postgres `--reuse-db`)
- [ ] Cobertura ≥ 80% em `accounts`, `health_logs`, `ai_engine`
- [ ] Testes de integração: cadastro → login → criar conversa → enviar mensagem → verificar histórico
- [ ] Testes de guardrail: ≥ 30 prompts adversariais, ≥ 95% detectados, ≤ 5% falsos positivos
- [ ] Testes de RAG: indexar doc fixture → query relevante retorna chunk; query off-topic retorna lista vazia
- [ ] LLM mockado em todos os testes (sem chamada real)
- [ ] CI passa em `.gitlab-ci.yml` (lint + test)

---

## Fora do Escopo (MVP)

| Item | Motivo |
|---|---|
| E-mail transacional (confirmação, reset) | Infra adicional desnecessária no MVP |
| Pagamento / planos | Validar produto antes de monetizar |
| Mobile app nativo | MVP é web/API-first |
| Multi-tenancy | Requer refatoração do modelo |
| SSO / OAuth | Menor prioridade para validação |
| Integração com wearables | Roadmap fase 3 |
| OCR de exames laboratoriais | Roadmap fase 4 |
| Frontend React | Cliente externo — outro repositório |

---

## Critérios de Aceite do MVP (Definition of Done)

- [ ] Usuário consegue cadastrar, logar, registrar dados de saúde e conversar com a IA via API
- [ ] IA responde com contexto de RAG e cita fontes quando aplicável
- [ ] Disclaimer aparece em respostas com viés clínico
- [ ] Pedidos de diagnóstico/prescrição são bloqueados antes de chegar ao LLM
- [ ] Admin sobe documento e vê `status=INDEXED`
- [ ] `docker compose up` sobe Django + Postgres + Chroma sem configuração extra
- [ ] Suite `pytest` passa, cobertura ≥ 80% nos apps críticos
- [ ] Nenhum secret hardcoded no código
- [ ] Fluxo end-to-end testado em ambiente local

---

*Próximo documento: [ARCHITECTURE.md](ARCHITECTURE.md)*

# MediClaw — Tasks (Roadmap Executável)

> Versão: 1.0 | Data: 2026-05-07
> Documento principal de execução. Marque `- [x]` ao concluir.
> Referência: [PRD.md](PRD.md) | [ARCHITECTURE.md](ARCHITECTURE.md)
> **Regra:** finalizar (com testes) o épico antes de iniciar o próximo.

---

## Mapeamento Plano-MVP → Épicos

| Plano-MVP | Épico | Arquivo |
|---|---|---|
| Etapa 1 — Planejamento e Infraestrutura | E1 — Foundation | [epics/epic-1-foundation.md](epics/epic-1-foundation.md) |
| Etapa 1 — Configuração de Segurança | E2 — Auth & Users | [epics/epic-2-auth.md](epics/epic-2-auth.md) |
| Etapa 2 — Backend e Core API | E3 — Health Logs | [epics/epic-3-core-api.md](epics/epic-3-core-api.md) |
| Etapa 3 — Camada de IA e Guardrails | E4 — AI Engine | [epics/epic-4-ai-engine.md](epics/epic-4-ai-engine.md) |
| Etapa 4 — Mecanismo RAG (núcleo) | E5.1 — RAG Essencial MVP | [epics/epic-5.1-rag-mvp.md](epics/epic-5.1-rag-mvp.md) |
| Etapa 4 — Mecanismo RAG (admin + testes) | E5.2 — RAG Final | [epics/epic-5.2-rag-final.md](epics/epic-5.2-rag-final.md) |
| Etapa 2 + Etapa 5 (lado backend) | E6 — Conversations & Chat | [epics/epic-6-chat.md](epics/epic-6-chat.md) |
| Etapa 6 — Testes, Avaliação e Refinamento | E7 — Testing & Hardening | [epics/epic-7-testing.md](epics/epic-7-testing.md) |

---

## Epic 1 — Foundation

> Pré-requisito de todos os demais. Bloqueante.

### Story 1.1 — Estrutura do projeto e settings
- [x] Mover `config/settings.py` para usar `python-dotenv` com fail-fast em envs obrigatórias
- [x] Criar `apps/common/` (exceptions, renderers, pagination, permissions, middleware)
- [x] Configurar DRF com renderer `{ data, error, meta }` e exception handler customizado
- [x] Configurar logging estruturado JSON com `request_id`
- [x] `python manage.py runserver` sem warnings críticos
- [x] Criar apps vazios: `accounts`, `health_logs`, `conversations`, `ai_engine`, `rag`, `audit`
- [x] Registrar `INSTALLED_APPS` e roteamento base em `config/urls.py` (`/api/v1/`)

### Story 1.2 — Healthcheck
- [x] `GET /health` retornando `{status, db, vector_store, version}`
- [x] Liveness check no Postgres (`SELECT 1`)
- [x] Stub de check do vector store (retorna `not_configured` até E5)

### Story 1.3 — CI básico
- [x] `.gitlab-ci.yml` rodando `pre-commit run --all-files` e `pytest`
- [x] Postgres como service no CI
- [x] Cache de pip configurado

---

## Epic 2 — Auth & Users

### Story 2.1 — Modelo User customizado
- [x] `User(AbstractUser)` com `email` único e `role`
- [x] `Profile` com `birth_date`, `biological_sex`, `height_cm`
- [x] `accepted_terms_at` no User
- [x] Manager customizado (`create_user`, `create_superuser`)
- [x] `AUTH_USER_MODEL` apontando para `accounts.User`
- [x] Migration inicial

### Story 2.2 — Endpoint de cadastro
- [x] `POST /api/v1/auth/register`
- [x] Serializer com validação de senha (≥ 8 chars, letra+dígito), e-mail único, `accept_terms=true`
- [x] Retorna `{access, refresh, user}`
- [x] Registra `USER_REGISTERED` no ActivityLog (stub)

### Story 2.3 — Endpoint de login + refresh
- [x] `POST /api/v1/auth/login` (custom view sobre `simplejwt`)
- [x] `POST /api/v1/auth/refresh`
- [x] Erros padronizados (`INVALID_CREDENTIALS`, `TOKEN_EXPIRED`)
- [x] Registra `LOGIN` no ActivityLog (stub)

### Story 2.4 — Endpoints /me
- [x] `GET /api/v1/auth/me` (sem `password`)
- [x] `PATCH /api/v1/auth/me` (campos editáveis: `name`, `profile.*`)
- [x] Permission `IsAuthenticated`

### Story 2.5 — Permissions e throttling
- [x] `IsAdminRole` em `apps/common/permissions.py`
- [x] `IsOwner` em `apps/common/permissions.py`
- [x] Throttle `anon=30/min`, `user=60/min` (configurado em settings)
- [x] Testes: token ausente → 401; role insuficiente → 403

---

## Epic 3 — Health Logs (Core API)

### Story 3.1 — Modelos
- [x] `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote`
- [x] Índices `(user, -<timestamp>)`
- [x] Migrations criadas (0001_initial)

### Story 3.2 — ViewSets CRUD
- [x] `WeightLogViewSet` (list, create, delete) — apenas registros do próprio usuário
- [x] Idem para Sleep, Activity, Nutrition
- [x] Filtros `from`, `to` via query params
- [x] Validações de domínio (peso 20–400, quality_score 1–10, note ≤1000 chars)

### Story 3.3 — Service de agregação
- [x] `services/aggregate.py::summarize(user_id, window_days)` retornando dict
- [x] `GET /api/v1/health/summary?window=7|30`
- [x] Cobertura de testes ≥ 90%

### Story 3.4 — Testes de integração
- [x] Cadastro → registro de logs → consulta `summary` produz valores esperados
- [x] Outro usuário não enxerga logs
- [x] 5 testes obrigatórios passando (5/5)

---

## Epic 4 — AI Engine & Guardrails

### Story 4.1 — Provider-agnóstico
- [x] `apps/ai_engine/providers/base.py::LLMProvider` (Protocol)
- [x] `OpenAIProvider` (usa `openai>=1.30`)
- [x] `GeminiProvider` (usa `google-generativeai>=0.8`) — substituiu Anthropic
- [x] `get_provider()` em `providers/__init__.py` lê `LLM_PROVIDER` (lazy imports)
- [x] `LLMProviderError` em `apps/common/exceptions.py`
- [x] Testes com mock do SDK

### Story 4.2 — System prompt e templates
- [x] `apps/ai_engine/prompts.py` com `SYSTEM_PROMPT_TEMPLATE`
- [x] Suporte a placeholders `{rag_context}`, `{health_summary}`
- [x] `DISCLAIMER` e `CITATION_LINE` como constantes reutilizáveis

### Story 4.3 — Guardrails determinísticos
- [x] `guardrails.check_input(text) → GuardrailResult`
- [x] Regex para diagnóstico, prescrição e urgência (urgência tem prioridade)
- [x] Mensagem educativa pré-definida para cada categoria de bloqueio
- [x] `guardrails.check_output(text)` valida resposta gerada
- [x] Suite de avaliação com 33 prompts (`tests/ai_eval/guardrails.yaml`)
- [x] TP=100%, FP=0% — metas atingidas (≥95% TP, ≤5% FP)

### Story 4.4 — Skills
- [x] `skills/bmi.py::calculate_bmi(weight_kg, height_cm)` com validação Pydantic
- [x] `skills/unit_convert.py::convert_units(value, from_unit, to_unit)` — 6 pares
- [x] `skills/health_summary.py` envolve `health_logs.aggregate.summarize`
- [x] Testes unitários com casos limite (10 para BMI, 8 para unit_convert)

### Story 4.5 — Orquestrador
- [x] `orchestrator.generate(user_id, conversation_id, query)` — não-stream
- [x] `orchestrator.generate_stream(...)` — gerador de eventos SSE-ready
- [x] Sequência: guardrail_pre → retriever → health_summary → prompt → llm → guardrail_post
- [x] Retorna `GenerateResult(content, tokens_used, blocked_by_guardrail, citations)`
- [x] Testes com LLM mockado (11 testes de orquestrador)

---

## Epic 5.1 — RAG Essencial (MVP)

> Núcleo do RAG: vector store, ingestão e retriever. Sem endpoints admin.

### Story 5.1.1 — Vector store
- [x] `apps/rag/vector_store.py::get_collection()` singleton com ChromaDB
- [x] Persistência em `CHROMA_PERSIST_DIR`
- [x] Healthcheck `vector_store: ok`

### Story 5.1.2 — Modelo KnowledgeDocument
- [x] Modelo + migration
- [x] Status enum (PROCESSING, INDEXED, ERROR)
- [x] `error_message` populado quando falhar

### Story 5.1.3 — Pipeline de ingestão
- [x] `ingestion.ingest(document, file_bytes)` síncrono
- [x] Suporte PDF (pypdf), MD/TXT (decode direto)
- [x] `RecursiveCharacterTextSplitter(chunk_size=1000, overlap=200)`
- [x] Embeddings via provider configurado
- [x] Metadados: `document_id`, `title`, `chunk_index`

### Story 5.1.4 — Retriever
- [x] `retriever.search(query, k=5, min_score=0.75) → list[dict]`
- [x] Retorna `[]` se coleção vazia
- [x] Filtro por score mínimo

### Story 5.1.5 — Healthcheck
- [x] `GET /health` retorna `vector_store: ok`
- [x] Atualiza stub da Story 1.2

---

## Epic 5.2 — RAG Final

> Pré-requisito: E5.1. Adiciona interface de curadoria e testes completos.
> Atualização 2026-05-31: base de conhecimento compartilhada — curadoria aberta a qualquer usuário autenticado (`IsAuthenticated`), não mais só admin.

### Story 5.2.1 — Endpoints de conhecimento
- [x] `POST /api/v1/admin/knowledge/upload` (multipart, ≤10MB, mimetypes válidos)
- [x] `GET /api/v1/admin/knowledge` (paginado)
- [x] `GET /api/v1/admin/knowledge/{id}/status`
- [x] `DELETE /api/v1/admin/knowledge/{id}` (remove chunks do Chroma)
- [x] Permission `IsAuthenticated` (era `IsAdminRole`); DELETE em PROCESSING → 409

### Story 5.2.2 — Validações e audit
- [x] Rejeita arquivo ausente, > 10 MB e mimetype inválido com codes corretos
- [x] Registra `KB_UPLOAD` e `KB_DELETE` no audit log

### Story 5.2.3 — Testes obrigatórios
- [x] 15 testes passando (ingestão, retriever, views/admin)

---

## Epic 6 — Conversations & Chat

### Story 6.1 — Modelos
- [x] `Conversation` (user, title, timestamps)
- [x] `Message` (conversation, role, content, tokens_used, blocked_by_guardrail, metadata)
- [x] Índice `(conversation, created_at)`
- [x] Migrations

### Story 6.2 — CRUD de conversas
- [x] `POST /api/v1/conversations/`
- [x] `GET /api/v1/conversations/` (paginado, ordenado por `updated_at desc`)
- [x] `GET /api/v1/conversations/{id}/` (inclui mensagens)
- [x] `DELETE /api/v1/conversations/{id}/`
- [x] Permission: `IsOwner`

### Story 6.3 — Envio de mensagem (não-stream)
- [x] Mensagem USER salva antes do stream
- [x] Mensagem ASSISTANT salva ao fim do stream
- [x] Validação: prompt vazio → 400; conversa ≥ 50 msgs → 400

### Story 6.4 — Streaming SSE
- [x] `GET /api/v1/conversations/{id}/stream?prompt=...&token=...`
- [x] Auth via `?token=` query param
- [x] Headers SSE corretos (`Cache-Control: no-cache`, `X-Accel-Buffering: no`)
- [x] Eventos: `token`, `citation`, `done`, `error`
- [x] Persiste mensagem ASSISTANT ao final do stream
- [x] Título da conversa gerado pelo primeiro prompt

### Story 6.5 — Triagem leve (opcional MVP)
- [ ] System prompt instrui a IA a fazer 2–3 perguntas estruturadas quando o usuário descreve sintoma
- [ ] Sem fluxo state-machine separado no MVP — apenas prompt engineering

### Story 6.6 — Conversa de boas-vindas (onboarding)
- [x] `apps/conversations/services/welcome.py::ensure_welcome_conversation(user)` cria conversa "Bem-vindo" no cadastro
- [x] Mensagem ASSISTANT reescrita (Epic 8): orienta o médico a iniciar consulta por chat, não pede dados do próprio médico
- [x] Skippada para usuários com `role=ADMIN`
- [x] Idempotente: não cria segunda conversa se já existe

### Story 6.7 — UserReadiness
- [x] `apps/ai_engine/skills/user_readiness.py::UserReadiness` (dataclass) — rastreia campos ausentes do Patient
- [x] `get_user_readiness(patient_id: int | None) → UserReadiness` — `None` retorna tudo faltando
- [x] `missing_labels_pt()` retorna labels em português
- [x] `to_metadata()` serializa para o evento `done` do SSE

### Story 6.8 — Captura automática de dados de saúde via chat
- [x] `apps/ai_engine/services/capture_models.py` — `ExtractedUserData`, `CaptureResult` (Pydantic) + campos `patient_id`, `patient_created`
- [x] `apps/ai_engine/services/capture_rules.py::parse_rules(text)` — regex para peso, altura, DOB, sexo, sono, atividade, nutrição, nome
- [x] `apps/ai_engine/services/capture_rules.py::message_likely_has_health_data(text)` — filtro de keywords antes do parse
- [x] `apps/ai_engine/services/data_extraction_llm.py` — fallback LLM quando regex não extrai
- [x] `apps/ai_engine/services/user_data_capture.py::capture_from_message(conversation_id, doctor_id, text) → CaptureResult`
- [x] Persiste automaticamente para `Patient`: WeightLog, SleepLog, ActivityLog, NutritionNote, first_name, profile fields
- [x] `CaptureResult.to_metadata()` incluído no evento SSE `done`
- [x] Testes atualizados em `tests/ai_engine/test_user_data_capture.py` (Patient-based)

---

## Epic 7 — Testing & Hardening

### Story 7.1 — Configuração pytest
- [x] `pytest.ini` com `DJANGO_SETTINGS_MODULE=config.settings`
- [x] `conftest.py` com fixtures: `api_client`, `user`, `admin_user`, `auth_client`
- [ ] Banco de teste reusável (`--reuse-db`)
- [x] Mock do LLM provider via `monkeypatch` nas suites que necessitam

### Story 7.2 — Suites
- [x] `tests/accounts/` — 13 testes: registro, login, /me, validações
- [x] `tests/health_logs/` — 5 testes: CRUD + summary
- [x] `tests/ai_engine/` — 78 testes: guardrails (25) + skills (18) + orquestrador (16) + user_data_capture (13) + user_readiness (6)
- [x] `tests/rag/` — 15 testes: ingestão (3) + retriever (4) + views admin (8)
- [x] `tests/conversations/` — 26 testes: CRUD+stream (21) + welcome (5)
- [ ] `tests/audit/` — métricas e logs (pendente)

### Story 7.3 — Avaliação dos guardrails
- [x] `tests/ai_eval/guardrails.yaml` com 33 prompts adversariais classificados
- [x] Script `tests/ai_eval/run.py` reporta TP/FP/FN
- [ ] CI roda a avaliação automaticamente

### Story 7.4 — Hardening
- [ ] `SECURE_*` settings habilitados quando `DEBUG=False`
- [ ] Headers de segurança via middleware Django padrão
- [ ] Testar `docker compose up` e fluxo end-to-end
- [ ] Documentar `README.md` com setup local e variáveis de ambiente
- [ ] Sanity check de secrets (sem hardcoded; `.env` no `.gitignore`)

### Story 7.5 — Documentação final
- [ ] Atualizar README com diagrama, links para specs e como rodar
- [ ] Atualizar este TASKS.md com check-marks ao concluir

---

## Epic 8 — Patient Management

> **Pivot arquitetural:** Introduz entidade `Patient` — médico atende pacientes; dados biométricos e conversas pertencem ao paciente, não ao médico.
> Referência: [epics/epic-8-patient.md](epics/epic-8-patient.md)

### Story 8.1 — Novo app `patients` e migrations

- [x] Criar `apps/patients/` com `Patient` model (doctor FK, first_name, birth_date, biological_sex, height_cm)
- [x] Constraint de unicidade: `unique_patient_name_dob_per_doctor` (nome+DOB por médico, quando DOB não é null)
- [x] Remover `Profile` de `accounts/models.py`
- [x] Alterar FK `user → patient` em WeightLog, SleepLog, ActivityLog, NutritionNote
- [x] Adicionar `patient` (FK nullable) e `deleted_at` em `Conversation`; renomear `user → doctor`
- [x] DB resetado (sem dados a preservar); migrations limpas geradas e aplicadas
- [x] Registrar `apps.patients` em `INSTALLED_APPS` e `config/urls.py`

### Story 8.2 — API de Pacientes

- [x] `PatientListSerializer` com `conversation_count`, `last_seen_at`, `latest_weight_kg` (via `_annotate_patients`)
- [x] `PatientDetailSerializer` com logs + conversas aninhadas
- [x] Views `list_patients` e `patient_detail` (GET/PATCH/DELETE) — filtradas por `doctor=request.user`
- [x] `GET /api/v1/patients/` — lista paginada com campos anotados
- [x] `GET /api/v1/patients/{id}/` — detalhe completo
- [x] `PATCH /api/v1/patients/{id}/` — atualiza campos do paciente
- [x] `DELETE /api/v1/patients/{id}/` — hard delete com cascade

### Story 8.3 — Soft Delete em Conversations

- [x] `ActiveConversationManager` com `get_queryset()` filtrando `deleted_at__isnull=True`
- [x] `Conversation.all_objects = models.Manager()` para acesso admin
- [x] `DELETE /api/v1/conversations/{id}/` seta `deleted_at = now()` (não apaga)
- [x] Queries de list e stream usam manager padrão (excluem soft-deleted)

### Story 8.4 — Captura de dados → Patient

- [x] Refatorar `capture_from_message(conversation_id, doctor_id, text)` — nova assinatura
- [x] `ensure_or_create_patient(doctor_id, conversation_id, first_name)` — cria ou vincula Patient na conversa
- [x] `resolve_patient_dob(conversation_id, doctor_id, birth_date)` — dedup por nome+DOB
- [x] Health logs salvos em `conversation.patient`, não em `User`
- [x] `CaptureResult` inclui `patient_id` e `patient_created`
- [x] Evento SSE `done` inclui `patient_id`, `patient_created`, `patient_first_name`
- [x] `UserReadiness` refatorado para ler dados de `Patient` (aceita `None` → tudo faltando)

### Story 8.5 — Conversation response inclui Patient

- [x] `_serialize_conversation` inclui `patient: {id, first_name}` (ou `null`)
- [x] `GET /api/v1/conversations/` retorna `patient: {id, first_name}` em cada item

### Story 8.6 — Testes

- [x] Testes de Patient integrados em `tests/ai_engine/test_user_readiness.py` (7 testes Patient-based)
- [x] Testes de captura em `tests/ai_engine/test_user_data_capture.py` (Patient + dedup + LLM merge)
- [x] Testes de soft delete em `tests/conversations/test_conversations.py` (soft delete, all_objects, 404)
- [x] 128 testes passando no total

---

## Definition of Done (Backend MVP)

- [x] Todas as user stories `Must` do PRD com testes passando (128 testes)
- [ ] Cobertura ≥ 80% em `accounts`, `health_logs`, `ai_engine` (não medida formalmente)
- [x] Avaliação de guardrails: script `tests/ai_eval/run.py` disponível com 33 prompts
- [ ] `docker compose up` sobe Django + Postgres + Chroma sem ajustes (Epic 7 pendente)
- [x] `GET /health` retorna `ok` para todos os subsistemas
- [ ] Documentação final atualizada (Epic 7 pendente)
- [ ] Code review com a checklist de segurança (Epic 7 pendente)

---

*Para cada épico, abra o arquivo correspondente em `epics/` para detalhes técnicos, schemas e exemplos.*

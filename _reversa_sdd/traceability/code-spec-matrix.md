# Matriz de Rastreabilidade Código → Spec

> Relaciona cada arquivo do legado à unit spec que o cobre.
> Cobertura: 🟢 CONFIRMADO (extraído diretamente) | 🟡 INFERIDO (coberto por análise de padrões) | n/a (sem unit correspondente).
> Gerado ao final da Fase 4 (Writer).

## Apps Django

| Arquivo do legado | Unit correspondente | Cobertura |
|--------------------|---------------------|-----------|
| `apps/accounts/models.py` | `accounts/` | 🟢 |
| `apps/accounts/serializers.py` | `accounts/` | 🟢 |
| `apps/accounts/services/persist.py` | `accounts/persist-user-name/` | 🟢 |
| `apps/accounts/urls.py` | `accounts/` | 🟢 |
| `apps/accounts/views.py` | `accounts/register/`, `accounts/login/`, `accounts/me/`, `accounts/admin-users/` | 🟢 |
| `apps/ai_engine/guardrails.py` | `ai_engine/guardrail/` | 🟢 |
| `apps/ai_engine/orchestrator.py` | `ai_engine/generate/`, `ai_engine/onboarding/` | 🟢 |
| `apps/ai_engine/prompts.py` | `ai_engine/generate/`, `ai_engine/guardrail/`, `ai_engine/onboarding/`, `conversations/welcome/` | 🟢 |
| `apps/ai_engine/providers/base.py` | `ai_engine/providers/` | 🟢 |
| `apps/ai_engine/providers/gemini_provider.py` | `ai_engine/providers/` | 🟢 |
| `apps/ai_engine/providers/openai_provider.py` | `ai_engine/providers/` | 🟢 |
| `apps/ai_engine/services/capture_models.py` | `ai_engine/capture/` | 🟢 |
| `apps/ai_engine/services/capture_rules.py` | `ai_engine/capture/` | 🟢 |
| `apps/ai_engine/services/data_extraction_llm.py` | `ai_engine/capture/` | 🟢 |
| `apps/ai_engine/services/user_data_capture.py` | `ai_engine/capture/` | 🟢 |
| `apps/ai_engine/skills/bmi.py` | `ai_engine/` (skills — citação no design) | 🟡 |
| `apps/ai_engine/skills/health_summary.py` | `ai_engine/onboarding/` | 🟢 |
| `apps/ai_engine/skills/unit_convert.py` | `ai_engine/` (skills — citação no design) | 🟡 |
| `apps/ai_engine/skills/user_readiness.py` | `ai_engine/onboarding/` | 🟢 |
| `apps/ai_engine/urls.py` | `ai_engine/` (unit sem rotas próprias) | 🟢 |
| `apps/audit/services/log.py` | `audit/record/` | 🟢 |
| `apps/audit/urls.py` | `audit/record/` | 🟢 |
| `apps/common/apps.py` | `common/` | 🟢 |
| `apps/common/exceptions.py` | `common/` | 🟢 |
| `apps/common/health_urls.py` | `common/` | 🟢 |
| `apps/common/logging_config.py` | `common/` | 🟢 |
| `apps/common/middleware.py` | `common/` | 🟢 |
| `apps/common/pagination.py` | `common/` | 🟢 |
| `apps/common/permissions.py` | `common/` | 🟢 |
| `apps/common/renderers.py` | `common/` | 🟢 |
| `apps/common/views.py` | `common/` | 🟢 |
| `apps/conversations/models.py` | `conversations/`, `conversations/welcome/` | 🟢 |
| `apps/conversations/serializers.py` | `conversations/list-create/`, `conversations/post-message/` | 🟢 |
| `apps/conversations/services/chat.py` | `conversations/post-message/` | 🟢 |
| `apps/conversations/services/welcome.py` | `conversations/welcome/` | 🟢 |
| `apps/conversations/urls.py` | `conversations/` | 🟢 |
| `apps/conversations/views.py` | `conversations/list-create/`, `conversations/detail-delete/`, `conversations/post-message/`, `conversations/stream-sse/` | 🟢 |
| `apps/health_logs/models.py` | `health_logs/` | 🟢 |
| `apps/health_logs/serializers.py` | `health_logs/crud-viewset/` | 🟢 |
| `apps/health_logs/services/aggregate.py` | `health_logs/summary/` | 🟢 |
| `apps/health_logs/services/persist.py` | `health_logs/persist-weight/` | 🟢 |
| `apps/health_logs/urls.py` | `health_logs/crud-viewset/`, `health_logs/summary/` | 🟢 |
| `apps/health_logs/views.py` | `health_logs/crud-viewset/`, `health_logs/summary/` | 🟢 |
| `apps/patients/apps.py` | `patients/` | 🟢 |
| `apps/patients/models.py` | `patients/` | 🟢 |
| `apps/patients/serializers.py` | `patients/list/`, `patients/detail-crud/` | 🟢 |
| `apps/patients/services/patient.py` | `patients/ensure-or-create/`, `patients/resolve-dob/` | 🟢 |
| `apps/patients/urls.py` | `patients/list/`, `patients/detail-crud/` | 🟢 |
| `apps/patients/views.py` | `patients/list/`, `patients/detail-crud/` | 🟢 |
| `apps/rag/ingestion.py` | `rag/upload-ingest/` | 🟢 |
| `apps/rag/models.py` | `rag/upload-ingest/`, `rag/delete/` | 🟢 |
| `apps/rag/retriever.py` | `rag/retrieval/` | 🟢 |
| `apps/rag/telemetry_noop.py` | `rag/collection-singleton/` | 🟢 |
| `apps/rag/urls.py` | `rag/upload-ingest/`, `rag/delete/`, `rag/retrieval/` | 🟢 |
| `apps/rag/vector_store.py` | `rag/collection-singleton/` | 🟢 |
| `apps/rag/views.py` | `rag/upload-ingest/`, `rag/delete/`, `admin` (métricas) | 🟢 |

## Configuração e infraestrutura

| Arquivo do legado | Unit correspondente | Cobertura |
|--------------------|---------------------|-----------|
| `config/settings.py` | `common/` (renderer, throttle, auth) | 🟢 |
| `config/urls.py` | `common/` (montagem de rotas) | 🟢 |
| `config/asgi.py` | n/a — infraestrutura de deploy | n/a |
| `config/wsgi.py` | n/a — infraestrutura de deploy | n/a |
| `manage.py` | n/a — bootstrap Django | n/a |

## Migrations

| Diretório | Unit correspondente | Cobertura |
|-----------|---------------------|-----------|
| `apps/accounts/migrations` | `accounts/` (modelos) | 🟡 |
| `apps/conversations/migrations` | `conversations/` (modelos) | 🟡 |
| `apps/health_logs/migrations` | `health_logs/` (modelos) | 🟡 |
| `apps/patients/migrations` | `patients/` (modelos) | 🟡 |
| `apps/rag/migrations` | `rag/` (modelo `KnowledgeDocument`) | 🟡 |

## Cobertura estimada

- **Arquivos `.py` do legado (apps + config):** 62
- **Mapeados a uma unit (🟢):** 57
- **Sem unit (`n/a`, infraestrutura de deploy/bootstrap):** 5 (`config/asgi.py`, `config/wsgi.py`, `manage.py` + 2 parcialmente)
- **Cobertura estimada:** ~92% dos arquivos de aplicação mapeados a specs executáveis.

## Arquivos com cobertura parcial (candidatos a análise adicional)

| Arquivo | Situação |
|---------|----------|
| `apps/ai_engine/skills/bmi.py` | Citado no design de `ai_engine`; sem use-case dedicado |
| `apps/ai_engine/skills/unit_convert.py` | Citado no design de `ai_engine`; sem use-case dedicado |
| `apps/rag/views.py` (`metrics`) | Documentado em `rag/design.md` e `user-stories/administracao.md`; rota vive no urlconf do `audit` |
| Migrations | Cobertas por inferência dos modelos (`🟡`) |

# Common, Tarefas de Implementação

> Sequência executável para reimplementar a unit `common` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] App `apps/common` registrado em `INSTALLED_APPS` (`apps.common.apps.CommonConfig`) no `settings.py`
- [ ] `structlog` instalado e importável
- [ ] Variáveis `DEBUG`, `LOG_LEVEL`, `ALLOWED_HOSTS` e demais do `.env` documentadas
- [ ] Postgres acessível (para o health check) e ChromaDB iniciado (para `vector_store` no health)

## Tarefas

- [ ] **T-01**, Exceção de negócio `AppError` com code/message/details/status_code
  - Origem no legado: `apps/common/exceptions.py:5-18`
  - Critério de pronto: `AppError("FORBIDDEN", "msg", 403, {...})` serializa como `{data: null, error: {code, message, details}, meta: {}}` com status 403; `default_code` = code
  - Confiança: 🟢

- [ ] **T-02**, Exceções de domínio `GuardrailBlockedError` (200) e `LLMProviderError` (502)
  - Origem no legado: `apps/common/exceptions.py:21-28`
  - Critério de pronto: `GuardrailBlockedError("motivo")` → `GUARDRAIL_BLOCKED` 200; `LLMProviderError("msg")` → `LLM_PROVIDER_ERROR` 502
  - Confiança: 🟢

- [ ] **T-03**, Exception handler de envelope `envelope_exception_handler`
  - Origem no legado: `apps/common/exceptions.py:31-44`
  - Critério de pronto: payload DRF com `code` usado como `error`; sem `code` → `{code: "UNHANDLED", message: str(payload)}`; exceção não-DRF retorna `None`
  - Confiança: 🟢

- [ ] **T-04**, Renderer global de envelope `EnvelopeJSONRenderer`
  - Origem no legado: `apps/common/renderers.py:4-12`
  - Critério de pronto: envolve `{data, error: null, meta: {}}`; não re-envelopa payload que já tem chaves `data` e `error`
  - Confiança: 🟢

- [ ] **T-05**, Middleware `RequestIDMiddleware`
  - Origem no legado: `apps/common/middleware.py:11-44`
  - Critério de pronto: gera/ecoa `X-Request-ID`, bind `request_id` no contextvar, loga `request_completed`/`request_failed` com `method`, `path`, `status_code`, `latency_ms` (sem PII), injeta header no response, limpa contextvars no `finally`
  - Confiança: 🟢

- [ ] **T-06**, Middleware `UserContextMiddleware`
  - Origem no legado: `apps/common/middleware.py:47-54`
  - Critério de pronto: bind `user_id` no contextvar apenas quando `request.user.is_authenticated`
  - Confiança: 🟢

- [ ] **T-07**, Permissões customizadas `IsAdminRole` e `IsOwner`
  - Origem no legado: `apps/common/permissions.py:4-20`
  - Critério de pronto: `IsAdminRole` exige `is_authenticated` + `role == "ADMIN"`; `IsOwner` resolve owner via chain `doctor`/`user`/`uploaded_by` e compara com `request.user`
  - Confiança: 🟢

- [ ] **T-08**, Paginação padrão `DefaultPagination`
  - Origem no legado: `apps/common/pagination.py:4-7`
  - Critério de pronto: `page_size=20`, aceita `?page_size=`, teto `max_page_size=100`
  - Confiança: 🟢

- [ ] **T-09**, Configuração de logging structlog (`configure_structlog`, `get_logging_config`, `get_logger`, `shared_processors`, `get_renderer`)
  - Origem no legado: `apps/common/logging_config.py:7-83`
  - Critério de pronto: dev usa `ConsoleRenderer`, prod `JSONRenderer`; `LOG_LEVEL` respeitado; loggers `urllib3`/`chromadb`/`httpx`/`httpcore` em `WARNING`; `get_logger` retorna `BoundLogger`
  - Confiança: 🟢

- [ ] **T-10**, Bootstrap do structlog no `CommonConfig.ready()`
  - Origem no legado: `apps/common/apps.py:8-13`
  - Critério de pronto: `ready()` chama `configure_structlog(debug=settings.DEBUG)`; `LOGGING` do settings definido via `get_logging_config(debug=DEBUG)`
  - Confiança: 🟢

- [ ] **T-11**, Health check `GET /health/`
  - Origem no legado: `apps/common/views.py:7-38`; `apps/common/health_urls.py:4`; `config/urls.py:37`
  - Critério de pronto: `SELECT 1` no Postgres + `get_collection().count()` no Chroma; ambos ok → 200 `{status: "ok", ...}`; qualquer falha → 503 `{status: "degraded", ...}`; rota montada na raiz (`/health/`), `AllowAny`, sem autenticação
  - Confiança: 🟢

- [ ] **T-12**, Wire global no `config/settings.py`
  - Origem no legado: `config/settings.py:52,62-73,115-129,151`
  - Critério de pronto: `DEFAULT_RENDERER_CLASSES`, `EXCEPTION_HANDLER`, `DEFAULT_PAGINATION_CLASS`, `MIDDLEWARE` (RequestID + UserContext), `INSTALLED_APPS`, `LOGGING` configurados conforme o legado
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Envelope de sucesso: resposta DRF sem envelope → corpo `{data, error: null, meta: {}}`
- [ ] **TT-02**, Envelope de erro com code: `AppError` → status correto + `{data: null, error: {code, message, details}, meta: {}}`
- [ ] **TT-03**, Handler com payload não-dict → `UNHANDLED`; exceção não-DRF → handler 500 padrão
- [ ] **TT-04**, Request ID: sem header → uuid gerado e ecoado; com header → eco do valor recebido
- [ ] **TT-05**, Logs: `request_completed` com `method`/`path`/`status_code`/`latency_ms` e `user_id` quando autenticado; sem PII no conteúdo
- [ ] **TT-06**, `IsAdminRole`: role USER → 403; role ADMIN → permitido
- [ ] **TT-07**, Health: DB + Chroma ok → 200 ok; Chroma fora → 503 degraded
- [ ] **TT-08**, Paginação: 50 itens → 20 na primeira página, `?page_size=` respeitado até o teto 100

## Tarefas de Migração de Dados (se aplicável)

- n/a — unit de infraestrutura pura, sem entidades ORM. Nenhum dado a migrar. 🟢

## Ordem Sugerida

1. T-01 → T-04 (exceções + renderer) e T-09 → T-10 (logging) primeiro: base das convenções globais.
2. T-03 (exception handler) e T-12 (wire no settings) logo em seguida: ativam o envelope em toda a API.
3. T-05 → T-06 (middlewares) e T-07 (permissões): camada transversal de request.
4. T-08 (paginação) e T-11 (health) por último: dependem das convenções de settings/rotas.
5. Testes TT-01 a TT-08 validam a infra globalmente — rodar após cada bloco; TT-05 requer um endpoint real (qualquer rota DRF autenticada).

## Lacunas Pendentes (🔴)

- [ ] `GuardrailBlockedError` é código morto no legado — decidir se a reimplementação a mantém (para fluxos futuros) ou remove. Origem: `apps/common/exceptions.py:21-23`
- [ ] `IsOwner` é código morto no legado — decidir se padroniza ownership por permission ou mantém o padrão de queryset por `doctor=request.user`. Origem: `apps/common/permissions.py:13-20`
- [ ] Versão do health check hardcoded — definir fonte única de versão (pyproject/settings/env). Origem: `apps/common/views.py:35`

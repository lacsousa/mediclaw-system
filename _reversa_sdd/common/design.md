# Common, Design Técnico

> Contrato operacional de **COMO** a unit `common` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

### Endpoints HTTP

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/health/` | — | `{status, db, vector_store, version}` | 200, 503 | `AllowAny` |

**Observação:** `/api/v1/health/` aponta para `health_logs.urls` (resumo agregado), não para este health check. A rota `GET /health/` é montada na raiz do host. 🟢

### Funções / classes

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `AppError` | `(code: str, message: str, status_code: int = 400, details: dict \| None = None)` | `APIException` | `detail = {code, message, details}`; `default_code` = code |
| `GuardrailBlockedError` | `(reason: str)` | `AppError` | `GUARDRAIL_BLOCKED`, status **200** |
| `LLMProviderError` | `(message: str)` | `AppError` | `LLM_PROVIDER_ERROR`, status **502** |
| `envelope_exception_handler` | `(exc, context)` | `Response \| None` | `None` para exceções não-DRF |
| `EnvelopeJSONRenderer.render` | `(data, accepted_media_type=None, renderer_context=None)` | `str` | Envelope `{data, error, meta}` |
| `RequestIDMiddleware.__call__` | `(request)` | `response` | Seta `request.request_id`, bind contextvar, loga latency |
| `UserContextMiddleware.__call__` | `(request)` | `response` | Bind `user_id` se autenticado |
| `IsAdminRole.has_permission` | `(request, view)` | `bool` | `is_authenticated` e `role == "ADMIN"` |
| `IsOwner.has_object_permission` | `(request, view, obj)` | `bool` | owner = `doctor` \| `user` \| `uploaded_by` |
| `DefaultPagination` | — | `PageNumberPagination` | `page_size=20`, `page_size_query_param="page_size"`, `max_page_size=100` |
| `health` | `(request)` | `Response` | DB + vector store → 200/503 |
| `configure_structlog` | `(*, debug: bool)` | `None` | Processors + renderer dev/prod |
| `get_logging_config` | `(*, debug: bool)` | `dict` | Dict de `LOGGING` do settings |
| `get_logger` | `(name: str)` | `BoundLogger` | Wrapper de `structlog.get_logger` |

## Fluxo Principal

### 1. Envelope de resposta (renderer global)

1. `EnvelopeJSONRenderer` é o `DEFAULT_RENDERER_CLASSES` — toda resposta DRF passa por ele. (`config/settings.py:120`) 🟢
2. Se `data` já é dict contendo `data` e `error`, renderiza intacto (anti-envelope duplo). (`apps/common/renderers.py:6-7`) 🟢
3. Senão, envolve: `{data: <conteúdo>, error: null, meta: {}}`. (`apps/common/renderers.py:8-11`) 🟢

### 2. Tratamento de exceções (envelope de erro)

1. `EXCEPTION_HANDLER` aponta para `envelope_exception_handler`. (`config/settings.py:128`) 🟢
2. Chama `rest_framework.views.exception_handler(exc, context)`. (`apps/common/exceptions.py:32`) 🟢
3. Se retorna `None` (exceção não tratada pelo DRF), repassa — cai no handler 500 do Django. (`apps/common/exceptions.py:33-34`) 🟢
4. Se `payload` é dict com `code`, usa como `error`; senão gera `{code: "UNHANDLED", message: str(payload)}`. (`apps/common/exceptions.py:36-42`) 🟢
5. Monta `{data: null, error: <payload>, meta: {}}`. 🟢

### 3. Request ID e latência (`RequestIDMiddleware`)

1. `structlog.contextvars.clear_contextvars()` no início da requisição. (`apps/common/middleware.py:16`) 🟢
2. Lê `X-Request-ID` do header ou gera `str(uuid.uuid4())`; grava em `request.request_id` e bind no contextvar. (`apps/common/middleware.py:17-19`) 🟢
3. Marca `start = time.perf_counter()`. (`apps/common/middleware.py:21`) 🟢
4. Chama `self.get_response(request)`; calcula `latency_ms`; loga `request_completed` com `method`, `path`, `status_code`, `latency_ms` — **sem PII**. (`apps/common/middleware.py:22-31`) 🟢
5. Injeta `response["X-Request-ID"] = rid`. (`apps/common/middleware.py:32`) 🟢
6. Em exceção, loga `request_failed` com `logger.exception` e relança. (`apps/common/middleware.py:34-42`) 🟢
7. `finally`: limpa contextvars. (`apps/common/middleware.py:43-44`) 🟢

### 4. Contexto de usuário (`UserContextMiddleware`)

- Se `request.user` está autenticado, bind `user_id=request.user.id` no contextvar → `merge_contextvars` adiciona ao log. (`apps/common/middleware.py:51-54`) 🟢

### 5. Health check (`GET /health/`)

1. `health` testa o Postgres com `connection.cursor()` executando `SELECT 1`. (`apps/common/views.py:20-25`) 🟢
2. `_vector_store_status` importa `get_collection` do rag e chama `.count()` — sucesso → `"ok"`, exceção → `"error"`. (`apps/common/views.py:7-14,27`) 🟢
3. `overall_ok = db_ok and vs_status == "ok"`; resposta `{status: ok|degraded, db, vector_store, version: "0.1.0"}` com 200/503. (`apps/common/views.py:28-37`) 🟢
4. Rota montada em `path("health/", include("apps.common.health_urls"))` na raiz (fora do `/api/v1/`). (`config/urls.py:37`) 🟢

### 6. Bootstrap de logging (`apps.py`)

1. `CommonConfig.ready()` chama `configure_structlog(debug=settings.DEBUG)` — roda a cada inicialização de worker/runserver, idempotente. (`apps/common/apps.py:8-13`) 🟢
2. `settings.LOGGING = get_logging_config(debug=DEBUG)` define o dict do Django logging. (`config/settings.py:151`) 🟢
3. Dev (`DEBUG=True`) usa `ConsoleRenderer` (legível); prod usa `JSONRenderer`. (`apps/common/logging_config.py:18-21`) 🟢
4. Loggers ruidosos (`urllib3`, `chromadb`, `httpx`, `httpcore`) silenciados em `WARNING`. (`apps/common/logging_config.py:74-77`) 🟢

## Fluxos Alternativos

- **[Payload de erro sem `code`]:** exceção DRF com payload não-dict ou sem `code` → `{code: "UNHANDLED", message: str(payload)}` — perde detalhe estruturado do erro. (`apps/common/exceptions.py:38-42`) 🟡
- **[Header `X-Request-ID` presente]:** middleware ecoa o valor recebido em vez de gerar `uuid4`. (`apps/common/middleware.py:17`) 🟢
- **[Chroma fora do ar no health]:** `get_collection().count()` lança → `vector_store: "error"` → `status: degraded` + 503, mesmo com DB ok. (`apps/common/views.py:13-14,28-29`) 🟢
- **[`GuardrailBlockedError` nunca lançada]:** o orquestrador de IA bloqueia via `GenerateResult(blocked=True)` em vez de lançar a exceção — a classe existe mas é código morto no legado. (`apps/common/exceptions.py:21-23`; `apps/ai_engine/orchestrator`) 🟢
- **[`IsOwner` sem uso]:** nenhuma view chama `IsOwner` — as views filtram `doctor=request.user` nas querysets. (`apps/common/permissions.py:13-20`) 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `rest_framework` | Renderer, exceptions, pagination, permissions | `JSONRenderer`, `APIException`, `exception_handler`, `PageNumberPagination`, `BasePermission` |
| `structlog` | Logging estruturado com contextvars | `merge_contextvars`, `stdlib.ProcessorFormatter`, `ConsoleRenderer`/`JSONRenderer`, `BoundLogger` |
| `django.db.connection` | Health check do Postgres | `connection.cursor()` → `SELECT 1` |
| `apps.rag.vector_store.get_collection` | Health check do vector store | `get_collection().count()` (import lazy, dentro da função) |
| `config/settings.py` | Wire global da unit | `DEFAULT_RENDERER_CLASSES`, `EXCEPTION_HANDLER`, `DEFAULT_PAGINATION_CLASS`, `MIDDLEWARE`, `LOGGING`, `INSTALLED_APPS` |
| `config/urls.py` | Montagem da rota de health | `path("health/", include("apps.common.health_urls"))` |
| Todos os apps | Consumo transversal | exceptions, permissions, logging_config, renderer/pagination (via settings) |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Contrato de resposta único `{data, error, meta}` via renderer + handler globais | `config/settings.py:120,128`; `renderers.py`; `exceptions.py` | 🟢 |
| Anti-envelope duplo por checagem de chaves `data`/`error` no renderer | `apps/common/renderers.py:6-7` | 🟢 |
| Exceção de negócio única `AppError` com `code` no `detail` | `apps/common/exceptions.py:5-18` | 🟢 |
| Request ID por header `X-Request-ID` ou `uuid4`, propagado no response | `apps/common/middleware.py:17,32` | 🟢 |
| Contexto de log por contextvars do structlog (request_id, user_id) | `apps/common/middleware.py:19,53`; `logging_config.py:9` | 🟢 |
| Logging sem PII — só metadados de request e `user_id` | `apps/common/middleware.py:25-31` | 🟢 |
| Bootstrap do structlog no `ready()` do app (idempotente, por worker) | `apps/common/apps.py:8-13` | 🟢 |
| Renderer do log: Console em dev, JSON em prod | `apps/common/logging_config.py:18-21` | 🟢 |
| Health check fora do `/api/v1/`, `AllowAny`, usado pelo Dockerfile.prod healthcheck | `config/urls.py:37`; `apps/common/views.py:18`; `django-api/Dockerfile.prod` | 🟢 |
| `IsOwner` via chain de `doctor`/`user`/`uploaded_by` | `apps/common/permissions.py:15-20` | 🟢 |
| Paginação `PageNumberPagination` com teto 100 e `page_size` por request | `apps/common/pagination.py:4-7` | 🟢 |
| Throttling global (anon/user/chat) declarado no settings | `config/settings.py:123-127` | 🟢 |
| Loggers de bibliotecas ruidosas em `WARNING` para reduzir ruído | `apps/common/logging_config.py:74-77` | 🟢 |
| Configuração de produção atrás de proxy (X-Forwarded-Proto, HSTS) no settings | `config/settings.py:170-180` | 🟢 |

## Estado Interno

- **Entidades ORM:** nenhuma. A unit é infraestrutura pura (classes, funções, middlewares). 🟢
- **Contexto por request** (não persistido): `request.request_id` (str), contextvars `request_id` e `user_id` do structlog — vivos apenas durante o ciclo da request, limpos no `finally`/`clear_contextvars`. 🟢
- **Configuração de runtime:** `LOG_LEVEL` (env, padrão `INFO`) define o nível de log raiz. 🟢

## Observabilidade

- Cada request loga `request_completed`/`request_failed` com `method`, `path`, `status_code`, `latency_ms` e contextvars `request_id` (+ `user_id` se autenticado). (`apps/common/middleware.py:25-31,36-39`) 🟢
- Falhas de request usam `logger.exception` (inclui traceback). (`apps/common/middleware.py:36`) 🟢
- **Lacuna:** falhas de autenticação e erros de negócio não geram eventos de auditoria (o `record()` do audit é stub — ADR-007). 🔴
- **Lacuna:** exceções não-DRF (500) passam pelo handler padrão do Django; o `request_failed` do middleware captura a latência, mas o corpo do 500 segue o formato padrão (fora do envelope). 🟡

## Riscos e Lacunas

- 🔴 `GuardrailBlockedError` é código morto — o guardrail bloqueia retornando `GenerateResult(blocked=True)`; manter apenas se houver plano de usá-la em fluxos não-stream.
- 🔴 `IsOwner` é código morto — nenhuma view a utiliza; as views filtram por `doctor=request.user` diretamente. Decidir se padroniza o ownership por permission ou remove.
- 🟡 Versão do health check hardcoded (`"0.1.0"` em `views.py:35`) — sem fonte única de versão; tende a desatualizar.
- 🟡 `envelope_exception_handler` com payload não-dict cai em `UNHANDLED` sem detalhe real do erro — aceitável no MVP, mas perde diagnóstico.
- 🟡 Health `AllowAny` exposto sem auth (intencional para probe), mas o endpoint `GET /health/` não está sob throttling anon — risco baixo de abuso.
- 🟡 Sem testes dedicados para `common` — infra configurada via settings, coberta indiretamente por integração.
- 🟢 Confirmado: `RequestIDMiddleware` usa `request.path` em logs (não URL com query) — evita vazar query strings sensíveis.

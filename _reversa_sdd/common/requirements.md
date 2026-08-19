# Common — Requisitos

> Contrato operacional da unit `common` (infraestrutura transversal do backend).
> Foco no **QUE** a unit entrega. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Infraestrutura transversal do MediClaw consumida por todos os apps: envelope de resposta padronizado `{data, error, meta}` (renderer + exception handler), exceções de negócio reutilizáveis (`AppError`, `GuardrailBlockedError`, `LLMProviderError`), middlewares de request ID e contexto de usuário, permissões customizadas (`IsAdminRole`, `IsOwner`), paginação padrão, configuração de logging estruturado via structlog (bootstrap no `ready()` do app) e health check de dependências (`GET /health/`). O wire acontece em `config/settings.py` (renderer, pagination, throttle, exception handler, middleware, LOGGING) e em `apps/common/apps.py` (configure_structlog no startup).

## Responsabilidades

- Envelopar toda resposta DRF em `{data, error: null, meta: {}}` via renderer global
- Normalizar exceções DRF e de negócio em `{data: null, error: {code, message, details}, meta: {}}`
- Definir exceções de negócio reutilizáveis com `code` e `status_code` customizados
- Correlacionar requisições via `X-Request-ID` (header recebido ou `uuid4`) e logar latência
- Enriquecer logs com `user_id` quando autenticado (contextvars do structlog)
- Fornecer gates de permissão: role `ADMIN` e ownership (`doctor`/`user`/`uploaded_by`)
- Paginação padrão da API (20 por página, até 100, `page_size` configurável por request)
- Configurar structlog (formatters, renderers, loggers ruidosos em WARNING) no bootstrap do app
- Expor `GET /health/` (AllowAny) verificando Postgres e vector store (Chroma)

## Regras de Negócio

- **RN-01** — Renderer só envolve a resposta se o payload **não** contiver as chaves `data` e `error`; se já tem envelope, passa intacto (evita envelope duplo). 🟢
- **RN-02** — Exception handler: payload DRF com chave `code` é usado como `error`; sem `code`, gera `{code: "UNHANDLED", message: str(payload)}`. 🟢 — **⚠️ Consequência (P-07):** `serializers.ValidationError` (de `is_valid(raise_exception=True)`) produz payload `{campo: [erros]}` **sem** `code` → vira `UNHANDLED`, não `VALIDATION_ERROR`. Isso contradiz os contratos `400 VALIDATION_ERROR` em health_logs, accounts e conversations. 🔴 requer decisão: normalizar `ValidationError` → `VALIDATION_ERROR` no handler. [Revisão Codex]
- **RN-03** — Exceções não tratadas pelo DRF fazem o handler retornar `None` → cai no handler 500 padrão do Django. 🟢
- **RN-04** — `GuardrailBlockedError` é lançada com HTTP **200** (bloqueio de guardrail não é erro de transporte). 🔴 (código morto — o orquestrador retorna `GenerateResult(blocked=True)` em vez de lançar)
- **RN-05** — `LLMProviderError` mapeia falha upstream do provedor para HTTP **502**. 🟢
- **RN-06** — Request ID: usa o header `X-Request-ID` se presente; senão gera `uuid4`; o mesmo valor é propagado no header do response. 🟢
- **RN-07** — Health: se Postgres **ou** vector store falhar, retorna `status: degraded` com HTTP **503**; ambos ok → `status: ok` 200. 🟢
- **RN-08** — `IsOwner`: owner é o primeiro atributo não-nulo de `doctor`, `user` ou `uploaded_by`; compara com `request.user`. 🟢
- **RN-09** — `IsAdminRole` exige `request.user.is_authenticated` **e** `role == "ADMIN"`. 🟢
- **RN-10** — Paginação padrão: 20 itens/página, `page_size` como query param, teto de 100. 🟢
- **RN-11** — Logs nunca contêm PII: middlewares logam apenas `method`, `path`, `status_code`, `latency_ms` e `user_id` (via contextvar). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Envelope padrão em toda resposta **DRF** (sucesso e erro) | Must | Toda resposta JSON produzida por views DRF tem forma `{data, error, meta}`; erro com `code` legível. **Escopo:** respostas DRF apenas — views Django puras (ex.: stream SSE `text/event-stream`) **não** passam pelo renderer |
| RF-02 | Exceção de negócio customizada com code, message, details e status_code | Must | `AppError("FORBIDDEN", "msg", 403)` serializa como `{data: null, error: {code: "FORBIDDEN", message: "msg", details: {}}, meta: {}}` com status 403 |
| RF-03 | Exceções de domínio: guardrail bloqueado (200) e erro de provider LLM (502) | Should | `GuardrailBlockedError("motivo")` → 200 `GUARDRAIL_BLOCKED`; `LLMProviderError("msg")` → 502 `LLM_PROVIDER_ERROR` |
| RF-04 | Request ID em toda requisição, propagado no response | Must | Requisição sem header → recebe `X-Request-ID` na resposta; com header → ecoa o mesmo valor |
| RF-05 | Enriquecimento de logs com contexto de usuário autenticado | Should | Logs emitidos durante request autenticada contêm `user_id` no campo estruturado. 🟡 — o bind acontece no middleware, **antes** da autenticação JWT do DRF (que ocorre na view); em requests Bearer o `request.user` pode ainda ser anônimo no momento do bind. Requer teste de integração para confirmar [Revisão Codex] |
| RF-06 | Permissões customizadas: `IsAdminRole` (role ADMIN) e `IsOwner` (ownership) | Must | View com `IsAdminRole` bloqueia role USER → 403; `IsOwner` valida dono do objeto |
| RF-07 | Paginação padrão aplicada nas listas DRF | Must | Lista retorna 20 itens por página, aceita `?page=`/`?page_size=` e respeita teto 100 |
| RF-08 | Logging estruturado via structlog, configurado no bootstrap | Must | App inicia com structlog ativo; dev usa ConsoleRenderer, prod JSONRenderer; `LOG_LEVEL` respeitado |
| RF-09 | Health check de dependências (DB + vector store) | Must | `GET /health/` retorna DRF `Response` → envelopado: `{data: {status, db, vector_store, version}, error: null, meta: {}}` com 200 (ok) ou 503 (degraded). 🟡 [Revisão Codex] |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Desempenho | Latência por request medida via `time.perf_counter` e logada em `latency_ms` | `apps/common/middleware.py:21-31` | 🟢 |
| Observabilidade | `request_id` bindado no middleware (🟢); `user_id` **tentado** no middleware — depende de `request.user` já autenticado, o que o JWT do DRF não garante nesse ponto | `apps/common/middleware.py:19,53`; `logging_config.py:74-77` | 🟡 [Revisão Codex] |
| Segurança | Logs sem PII — apenas metadados de request (`method`, `path`, `status_code`, `latency_ms`) | `apps/common/middleware.py:25-31` | 🟢 |
| Segurança | Throttling global configurado (anon 30/min, user 60/min, chat 10/min) | `config/settings.py:123-127` | 🟢 |
| Disponibilidade | Health check vira 503 quando dependência (DB ou Chroma) falha | `apps/common/views.py:28-37` | 🟢 |

## Critérios de Aceitação

```gherkin
# Envelope de sucesso
Dado uma resposta DRF qualquer (ex.: lista paginada)
Quando o renderer serializa a resposta
Então o corpo tem a forma {data, error: null, meta} e o conteúdo original fica em data

# Envelope de erro com code
Dado uma AppError lançada com code, message, details e status 403
Quando o exception handler processa a exceção
Então a resposta tem status 403 e corpo {data: null, error: {code, message, details}, meta: {}}

# Erro não-DRF
Dado uma exceção não tratada pelo DRF (ex.: RuntimeError)
Quando o exception handler processa
Então retorna None e o Django aplica o handler 500 padrão

# Request ID — ausente
Dado uma requisição sem header X-Request-ID
Quando o middleware processa a requisição
Então um uuid é gerado, logado como request_id e devolvido no header X-Request-ID do response

# Request ID — presente
Dado uma requisição com header X-Request-ID: abc-123
Quando o middleware processa a requisição
Então o response retorna X-Request-ID: abc-123 (eco do header de entrada)

# Health — tudo ok
Dado Postgres e ChromaDB respondendo
Quando faço GET /health/
Então recebo 200 com {data: {status: "ok", db: "ok", vector_store: "ok", version: "0.1.0"}, error: null, meta: {}}

# Health — degradado
Dado o ChromaDB fora do ar
Quando faço GET /health/
Então recebo 503 com {data: {status: "degraded", db: "ok", vector_store: "error"}, error: null, meta: {}}

# IsAdminRole — sem role
Dado um usuário autenticado com role USER
Quando acessa uma rota com IsAdminRole
Então recebo 403 FORBIDDEN

# Paginação padrão
Dado uma lista com 50 itens via endpoint paginado
Quando faço GET sem parâmetros de página
Então recebo 20 itens na primeira página e metadados de paginação
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Envelope de resposta (renderer + handler) | Must | Contrato de resposta do projeto; todas as rotas dependem |
| `AppError` + exceções de domínio | Must | Base de todos os códigos de erro da API (`FORBIDDEN`, `NOT_FOUND`, etc.) |
| Request ID e contexto de usuário | Must | Correlação de logs e observabilidade em produção |
| Permissões `IsAdminRole`/`IsOwner` | Must | `IsAdminRole` é o gate da rota admin; `IsOwner` padrão de ownership |
| Paginação padrão | Should | Aplicável às listas, com fallback em paginação manual existente em alguns endpoints |
| Logging estruturado structlog | Must | Observabilidade sem PII; configuração global no bootstrap |
| Health check | Should | Probe/load balancer e healthcheck do Dockerfile.prod |
| `GuardrailBlockedError` (200) | Could | Código morto no legado — guardrail bloqueia via `GenerateResult(blocked=True)` |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/common/exceptions.py` | `AppError`, `GuardrailBlockedError`, `LLMProviderError`, `envelope_exception_handler` | 🟢 |
| `apps/common/renderers.py` | `EnvelopeJSONRenderer` | 🟢 |
| `apps/common/middleware.py` | `RequestIDMiddleware`, `UserContextMiddleware` | 🟢 |
| `apps/common/permissions.py` | `IsAdminRole`, `IsOwner` | 🟢 |
| `apps/common/pagination.py` | `DefaultPagination` | 🟢 |
| `apps/common/logging_config.py` | `configure_structlog`, `get_logging_config`, `get_logger`, `shared_processors`, `get_renderer` | 🟢 |
| `apps/common/views.py` | `health`, `_vector_store_status` | 🟢 |
| `apps/common/health_urls.py` | rota `GET /health/` | 🟢 |
| `apps/common/apps.py` | `CommonConfig.ready` → `configure_structlog` | 🟢 |
| `config/settings.py` | `REST_FRAMEWORK` (renderer, pagination, throttle, exception handler), `MIDDLEWARE`, `LOGGING`, `INSTALLED_APPS` | 🟢 |
| `config/urls.py` | montagem de `health/` | 🟢 |

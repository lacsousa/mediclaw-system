# Epic 1 — Foundation

> **Plano-MVP Etapa 1.** Bootstrapping do projeto Django: settings, banco, common utils, healthcheck, CI.
> **Bloqueante** para todos os demais épicos.
> Referência: [PRD §EPIC-01](../PRD.md) · [TASKS §Epic 1](../TASKS.md#epic-1--foundation)

---

## Objetivo

Estabelecer a base do backend para que os apps de domínio possam ser desenvolvidos em paralelo a partir de E2.

## Escopo

- Estrutura de apps Django
- Settings com fail-fast em envs obrigatórias
- Renderer e exception handler `{ data, error, meta }`
- Logging estruturado com `request_id`
- Healthcheck e CI básico

## Fora do escopo

- Modelo de usuário (E2)
- Domínio de saúde, IA, RAG (E3+)

---

## Stories

### Story 1.1 — Estrutura e settings

**O quê:** Reorganizar `config/settings.py`, criar apps vazios e `apps/common/`.

**Passos:**

1. Atualizar `requirements.txt` adicionando dependências:
   ```txt
   pypdf>=4.0
   pydantic>=2.7
   chromadb==0.5.*
   langchain==0.3.*
   langchain-openai==0.3.*
   langchain-anthropic==0.3.*
   langchain-community==0.3.*
   openai>=1.30
   anthropic>=0.34
   uvicorn[standard]>=0.30
   pytest==8.*
   pytest-django==4.*
   ```
2. Criar diretórios:
   ```
   apps/
     __init__.py
     common/
     accounts/
     health_logs/
     conversations/
     ai_engine/
     rag/
     audit/
   ```
3. `apps/common/exceptions.py`:
   ```python
   from rest_framework.exceptions import APIException
   from rest_framework.views import exception_handler

   class AppError(APIException):
       status_code = 400
       default_code = "APP_ERROR"
       def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
           self.status_code = status_code
           self.default_code = code
           self.detail = {"code": code, "message": message, "details": details or {}}

   class GuardrailBlockedError(AppError):
       def __init__(self, reason: str):
           super().__init__("GUARDRAIL_BLOCKED", reason, 200)

   class LLMProviderError(AppError):
       def __init__(self, message: str):
           super().__init__("LLM_PROVIDER_ERROR", message, 502)

   def envelope_exception_handler(exc, context):
       response = exception_handler(exc, context)
       if response is None:
           return None
       payload = response.data
       if isinstance(payload, dict) and "code" in payload:
           response.data = {"data": None, "error": payload, "meta": {}}
       else:
           response.data = {"data": None, "error": {"code": "UNHANDLED", "message": str(payload)}, "meta": {}}
       return response
   ```
4. `apps/common/renderers.py`:
   ```python
   from rest_framework.renderers import JSONRenderer

   class EnvelopeJSONRenderer(JSONRenderer):
       def render(self, data, accepted_media_type=None, renderer_context=None):
           if isinstance(data, dict) and {"data", "error"} <= set(data.keys()):
               return super().render(data, accepted_media_type, renderer_context)
           return super().render({"data": data, "error": None, "meta": {}}, accepted_media_type, renderer_context)
   ```
5. `apps/common/pagination.py`:
   ```python
   from rest_framework.pagination import PageNumberPagination
   class DefaultPagination(PageNumberPagination):
       page_size = 20
       page_size_query_param = "page_size"
       max_page_size = 100
   ```
6. `apps/common/middleware.py`:
   ```python
   import uuid, logging
   logger = logging.getLogger(__name__)

   class RequestIDMiddleware:
       def __init__(self, get_response): self.get_response = get_response
       def __call__(self, request):
           rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
           request.request_id = rid
           response = self.get_response(request)
           response["X-Request-ID"] = rid
           return response
   ```
7. `config/settings.py` (trechos relevantes):
   ```python
   import os
   from pathlib import Path
   from datetime import timedelta
   from dotenv import load_dotenv
   load_dotenv()

   def _required(name: str) -> str:
       v = os.environ.get(name)
       if not v: raise RuntimeError(f"Missing required env: {name}")
       return v

   SECRET_KEY = _required("SECRET_KEY")
   DEBUG = os.environ.get("DEBUG", "False") == "True"
   ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

   INSTALLED_APPS = [
       "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
       "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
       "rest_framework", "corsheaders",
       "apps.common", "apps.accounts", "apps.health_logs",
       "apps.conversations", "apps.ai_engine", "apps.rag", "apps.audit",
   ]

   MIDDLEWARE = [
       "apps.common.middleware.RequestIDMiddleware",
       "corsheaders.middleware.CorsMiddleware",
       "django.middleware.security.SecurityMiddleware",
       # ... padrão do Django
   ]

   REST_FRAMEWORK = {
       "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
       "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
       "DEFAULT_RENDERER_CLASSES": ["apps.common.renderers.EnvelopeJSONRenderer"],
       "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.DefaultPagination",
       "PAGE_SIZE": 20,
       "DEFAULT_THROTTLE_CLASSES": [
           "rest_framework.throttling.AnonRateThrottle",
           "rest_framework.throttling.UserRateThrottle",
       ],
       "DEFAULT_THROTTLE_RATES": {"anon": "30/min", "user": "60/min", "chat": "10/min"},
       "EXCEPTION_HANDLER": "apps.common.exceptions.envelope_exception_handler",
   }

   SIMPLE_JWT = {
       "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_MINUTES", "30"))),
       "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("REFRESH_TOKEN_DAYS", "1"))),
       "AUTH_HEADER_TYPES": ("Bearer",),
   }

   LOGGING = {
       "version": 1, "disable_existing_loggers": False,
       "formatters": {"json": {"format": '{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s","logger":"%(name)s"}'}},
       "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
       "root": {"handlers": ["console"], "level": "INFO"},
   }
   ```
8. `config/urls.py`:
   ```python
   from django.contrib import admin
   from django.urls import path, include
   urlpatterns = [
       path("admin/", admin.site.urls),
       path("api/v1/auth/", include("apps.accounts.urls")),
       path("api/v1/health/", include("apps.health_logs.urls")),
       path("api/v1/conversations/", include("apps.conversations.urls")),
       path("api/v1/admin/knowledge/", include("apps.rag.urls")),
       path("api/v1/admin/", include("apps.audit.urls")),
       path("health", include("apps.common.health_urls")),
   ]
   ```

**Definition of Done:**
- [ ] `python manage.py runserver` sobe sem erros
- [ ] Resposta de qualquer rota DRF segue o envelope `{ data, error, meta }`
- [ ] `pre-commit run --all-files` verde

---

### Story 1.2 — Healthcheck

**O quê:** Endpoint `GET /health` que valida Postgres e (futuramente) ChromaDB.

**Implementação:**

```python
# apps/common/views.py
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    db_ok = True
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:
        db_ok = False
    return Response({
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "vector_store": "not_configured",
        "version": "0.1.0",
    }, status=200 if db_ok else 503)
```

```python
# apps/common/health_urls.py
from django.urls import path
from .views import health
urlpatterns = [path("", health)]
```

**Definition of Done:**
- [ ] `curl http://localhost:8000/health` retorna 200 com payload esperado
- [ ] Quando Postgres está fora, retorna 503

---

### Story 1.3 — CI

**O quê:** Atualizar `.gitlab-ci.yml` para rodar `pre-commit` e `pytest`.

```yaml
# .gitlab-ci.yml (resumo)
stages: [lint, test]

lint:
  stage: lint
  image: python:3.12-slim
  script:
    - pip install pre-commit
    - pre-commit run --all-files

test:
  stage: test
  image: python:3.12-slim
  services:
    - postgres:16-alpine
  variables:
    POSTGRES_DB: mediclaw
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    DB_HOST: postgres
    SECRET_KEY: ci-secret-min-50-chars-aaaaaaaaaaaaaaaaaaaaaaaaa
  script:
    - pip install -r requirements.txt
    - pytest -q --reuse-db
```

**Definition of Done:**
- [ ] CI verde no MR
- [ ] `pytest` roda mesmo sem testes (saída "no tests collected" não falha)

---

## Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Settings divergente entre dev/CI/prod | `_required()` no boot detecta envs faltando |
| LangChain quebrar entre minor versions | Pinos `0.3.*` no `requirements.txt`; isolar uso em `ai_engine` e `rag` |
| Logs vazando PII | `LOGGING` formatter ignora payload de `body`; código nunca loga `content` de mensagens |

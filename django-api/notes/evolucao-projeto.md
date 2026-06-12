# Evolução do Projeto

## 2026-05-21 — Epic 4 (AI Engine & Guardrails) Completo ✓

### O que foi implementado

Epic 4 entrega a camada de IA do MediClaw: providers de LLM intercambiáveis, guardrails de segurança determinísticos, skills de cálculo e o orquestrador central.

**Providers (`apps/ai_engine/providers/`)**
- ✅ `base.py` — `LLMProvider` Protocol + `ChatMessage` TypedDict
- ✅ `openai_provider.py` — OpenAI (stream + complete), wraps erros em `LLMProviderError`
- ✅ `gemini_provider.py` — Google Gemini, converte `assistant→model`, separa system instruction
- ✅ `providers/__init__.py` — factory `get_provider()` com **lazy imports** (sem depender dos dois SDKs ao mesmo tempo)
- Troca de provider: apenas set `LLM_PROVIDER=openai|gemini` no `.env`

**Guardrails (`apps/ai_engine/guardrails.py`)**
- ✅ `check_input(text)` — detecta urgência (prioridade máxima) → diagnóstico → prescrição
- ✅ `check_output(text)` — detecta diagnósticos/prescrições na resposta gerada pelo LLM
- ✅ Mensagens educativas distintas para cada categoria de bloqueio
- ✅ Eval set de 33 prompts (`tests/ai_eval/guardrails.yaml`) — **TP=100%, FP=0%**
- ✅ Script `tests/ai_eval/run.py` calcula TP/FP/FN e falha se abaixo das metas

**Skills (`apps/ai_engine/skills/`)**
- ✅ `bmi.py::calculate_bmi(weight_kg, height_cm)` — 6 categorias + validação Pydantic
- ✅ `unit_convert.py::convert_units(value, from_unit, to_unit)` — kg↔lb, cm↔in, ml↔fl_oz
- ✅ `health_summary.py` — wrapper que chama `aggregate.summarize()` (contrato E3→E4)

**Orquestrador (`apps/ai_engine/orchestrator.py`)**
- ✅ `generate(user_id, conversation_id, query) → GenerateResult` — não-stream
- ✅ `generate_stream(user_id, conversation_id, query) → Iterator[dict]` — eventos SSE-ready
- ✅ Sequência: guardrail_pre → RAG retriever (stub) → health_summary → system prompt → LLM → guardrail_post → disclaimer
- ✅ Disclaimer obrigatório injetado automaticamente (sem duplicação)

**Stubs criados para dependências futuras**
- `apps/conversations/models.py` — `Conversation` + `Message` mínimos (Epic 6 vai estender)
- `apps/rag/retriever.py` — `search()` retorna lista vazia (Epic 5 vai implementar)
- Migration `conversations/0001_initial` criada e aplicada

**Testes (49/49 passando + 65/65 na suite completa)**
- ✅ `tests/ai_engine/test_guardrails.py` — 20 testes (check_input + check_output)
- ✅ `tests/ai_engine/test_skills.py` — 18 testes (BMI + unit_convert)
- ✅ `tests/ai_engine/test_orchestrator.py` — 11 testes (geração, bloqueio, stream)

### Como testar os guardrails

```bash
# Rodar o eval harness:
uv run python tests/ai_eval/run.py
# Saída esperada: TP=100.0%, FP=0.0%, PASS

# Rodar suite de unit tests:
uv run pytest tests/ai_engine/ -v
```

### Como usar o orquestrador (sem API real)

```python
import os
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "sk-..."

from apps.ai_engine.orchestrator import generate

result = generate(user_id=1, conversation_id=0, query="Como melhorar meu sono?")
print(result.content)         # resposta com disclaimer
print(result.blocked_by_guardrail)  # False
print(result.tokens_used)     # tokens consumidos

# Pergunta bloqueada por guardrail:
result = generate(user_id=1, conversation_id=0, query="Que remédio devo tomar?")
print(result.blocked_by_guardrail)  # True — sem chamar o LLM
```

---

## 2026-05-21 — Correção: rota de criação de usuário por admin

### Problema identificado

Ao tentar usar a aplicação pela primeira vez, foi detectado que:

1. **Superusuários criados via `createsuperuser` não possuem `Profile`** — o Django Admin
   não passa pelo serializer da API, então o registro é criado diretamente no banco sem o
   objeto `Profile`. Qualquer chamada a `GET /api/v1/auth/me` com esse usuário resulta em
   erro 500 (`RelatedObjectDoesNotExist`).

2. **Ausência de rota para admin criar outros usuários** — o único endpoint de cadastro era
   `POST /api/v1/auth/register`, que exige `accept_terms: true` por ser voltado ao usuário
   final. Não havia como um administrador criar contas sem simular o fluxo de auto-cadastro.

### O que foi corrigido e implementado

**Nova rota: `POST /api/v1/admin/users`** (requer role `ADMIN`)

Permite que um administrador autenticado crie usuários sem os campos de consentimento LGPD
do fluxo público. O `Profile` é criado automaticamente junto com o usuário.

Campos aceitos:

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `email` | string | sim | único, normalizado para lowercase |
| `password` | string | sim | ≥ 8 chars, letra + dígito |
| `name` | string | sim | máximo 120 chars |
| `role` | `"USER"` ou `"ADMIN"` | não | padrão `"USER"` |

**Arquivos modificados:**

- `apps/accounts/serializers.py` — adicionado `AdminCreateUserSerializer`
- `apps/accounts/views.py` — adicionada view `admin_create_user` com `@permission_classes([IsAdminRole])`
- `apps/audit/urls.py` — antes vazio; agora registra `path("users", admin_create_user)`

A rota `/api/v1/admin/` já estava mapeada em `config/urls.py` para `apps.audit.urls`,
então nenhuma alteração foi necessária no roteamento raiz.

### Como usar

#### 1. Corrigir superusuário existente sem Profile

Se você criou o admin via `createsuperuser`, rode no shell Django:

```bash
python manage.py shell
```

```python
from apps.accounts.models import User, Profile
admin = User.objects.get(email="admin@admin.com")
Profile.objects.get_or_create(user=admin)
```

#### 2. Logar como admin para obter token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "<sua-senha>"}'
```

Salve o `access` token:

```bash
ADMIN_TOKEN="<access-token-do-admin>"
```

#### 3. Criar novo usuário via rota de admin

```bash
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novo@example.com",
    "password": "Senha123",
    "name": "Novo Usuário",
    "role": "USER"
  }'
```

Resposta (201):
```json
{
  "data": {
    "id": 2,
    "email": "novo@example.com",
    "first_name": "Novo Usuário",
    "role": "USER",
    "accepted_terms_at": null,
    "profile": { "birth_date": null, "biological_sex": null, "height_cm": null }
  },
  "error": null,
  "meta": {}
}
```

#### 4. Tentar sem ser admin → 403

```bash
# Com token de usuário USER normal:
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "x@x.com", "password": "Senha123", "name": "X"}'
# → 403 Forbidden
```

### Diferença entre as duas rotas de criação

| | `POST /api/v1/auth/register` | `POST /api/v1/admin/users` |
|---|---|---|
| Quem pode usar | Qualquer um (público) | Apenas admins (Bearer token com role ADMIN) |
| `accept_terms` | Obrigatório e deve ser `true` | Não existe — admin é isento |
| `accepted_terms_at` | Gravado com `timezone.now()` | Fica `null` |
| `role` | Sempre `USER` | Admin pode definir `USER` ou `ADMIN` |
| `Profile` criado | Sim | Sim |

---

## 2026-05-21 — Epic 3 (Core API — Health Logs) Completo ✓

### O que foi desenvolvido
Epic 3 foi concluído com CRUD completo de dados biométricos e service de agregação que alimenta a IA.

**Modelos criados** (`apps/health_logs/models.py`)
- ✅ `WeightLog` — `value_kg` (Decimal 5,2), `measured_at`, índice `["user", "-measured_at"]`
- ✅ `SleepLog` — `duration_hours` (Decimal 4,2), `quality_score` (1–10), `started_at`
- ✅ `ActivityLog` — `type` (CharField 40), `duration_min`, `performed_at`
- ✅ `NutritionNote` — `note` (TextField), `logged_at`

**Service de Agregação** (`apps/health_logs/services/aggregate.py`)
- ✅ Função `summarize(user_id, window_days=7)` retorna:
  - `avg_sleep_hours`, `avg_sleep_quality` — médias no window
  - `latest_weight_kg`, `weight_trend_kg` — último peso e tendência
  - `total_activity_min` — soma de atividade no window
  - `last_nutrition_notes` — últimas 3 notas
  - Todos os campos retornam `None` quando sem dados (nunca erro)

**Serializers** (`apps/health_logs/serializers.py`)
- ✅ `_BaseOwnedSerializer` — injeta `user` do request no `create`
- ✅ `WeightLogSerializer` — valida peso 20–400 kg e `measured_at` não futuro
- ✅ `SleepLogSerializer` — valida `quality_score` entre 1–10
- ✅ `ActivityLogSerializer` — valida `duration_min >= 1`
- ✅ `NutritionNoteSerializer` — valida `note` ≤ 1000 caracteres

**ViewSets** (`apps/health_logs/views.py`)
- ✅ Mixin `_OwnedQuerysetMixin` — filtra por `user=request.user`, aceita `from`/`to`
- ✅ 4 ViewSets (Weight, Sleep, Activity, Nutrition) com GET/POST/DELETE
- ✅ Endpoint `health_summary` — `GET /api/v1/health/summary?window=7|30`

**Endpoints**
- ✅ `GET/POST/DELETE /api/v1/health/weight/` — gerenciar pesos
- ✅ `GET/POST/DELETE /api/v1/health/sleep/` — gerenciar sono
- ✅ `GET/POST/DELETE /api/v1/health/activity/` — gerenciar atividades
- ✅ `GET/POST/DELETE /api/v1/health/nutrition/` — gerenciar notas nutricionais
- ✅ `GET /api/v1/health/summary` — agregação para IA

**Testes (5/5 passando)**
- ✅ `test_summary_with_no_logs_returns_nulls` — verifica campos None/0 sem dados
- ✅ `test_summary_aggregates_within_window` — cria logs e valida agregações
- ✅ `test_summary_excludes_other_users` — isolamento de dados entre usuários
- ✅ `test_weight_log_validates_range` — validação de peso fora do intervalo
- ✅ `test_user_cannot_delete_another_users_log` — validação de ownership

**CI/Code Quality**
- ✅ `pytest tests/ -v` — 16/16 testes passando (11 auth + 5 health_logs) em 2.47s
- ✅ `django check` — sem erros
- ✅ `pre-commit` — verde (black + linters)
- ✅ Migration `0001_initial` criada
- ✅ Novo fixture: `other_user`, `freezer` (freezegun)

---

## 2026-05-21 — Epic 2 (Auth & Users) Completo ✓

### O que foi desenvolvido
Epic 2 foi concluído com modelo de usuário customizado, autenticação JWT, perfil personalizado e consentimento LGPD.

**Modelos e Banco de Dados**
- ✅ `User` customizado com email como USERNAME_FIELD
- ✅ `UserManager` com `create_user` e `create_superuser`
- ✅ Roles (USER/ADMIN) com validação
- ✅ `accepted_terms_at` para registro de consentimento LGPD
- ✅ `Profile` OneToOne com bio, sexo, altura
- ✅ Migration inicial criada e funcional
- ✅ `AUTH_USER_MODEL = "accounts.User"` em settings

**Serializers**
- ✅ `RegisterSerializer` — validação de senha (≥8 chars, letra+dígito), accept_terms obrigatório, email duplicado
- ✅ `UserSerializer` — retorna id, email, name, role, accepted_terms_at, profile
- ✅ `ProfileSerializer` — birth_date, biological_sex, height_cm

**Endpoints**
- ✅ `POST /api/v1/auth/register` — criar account com tokens JWT (status 201)
- ✅ `POST /api/v1/auth/login` — autenticar e retornar tokens (status 200)
- ✅ `POST /api/v1/auth/refresh` — renovar access token (SimpleJWT)
- ✅ `GET /api/v1/auth/me` — dados do usuário autenticado (requer token)
- ✅ `PATCH /api/v1/auth/me` — atualizar nome e profile (requer token)

**Permissions**
- ✅ `IsAdminRole` — valida role=="ADMIN"
- ✅ `IsOwner` — valida propriedade de objetos

**Testes (11/11 passando)**
- ✅ Register: criação de user com tokens, rejeição de senha fraca, validação de accept_terms, email duplicado
- ✅ Login: sucesso com tokens, erro 401 com senha errada, erro 401 com user inativo
- ✅ Me: requer autenticação, GET retorna dados, PATCH atualiza nome e profile

**CI/Code Quality**
- ✅ `pytest` 11/11 testes passando (1.75s)
- ✅ `django check` sem erros
- ✅ `pre-commit` verde (black formatou arquivos)
- ✅ `pyproject.toml` atualizado com todas as dependências

---

## 📝 Como testar a API — Exemplos práticos

### Pré-requisito
Certifique-se que o servidor está rodando:
```bash
python manage.py runserver
# ou em devcontainer:
cd /workspace && python manage.py runserver 0.0.0.0:8000
```

### 1. Cadastro de novo usuário

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria@example.com",
    "password": "SecurePass123",
    "name": "Maria Silva",
    "accept_terms": true
  }'
```

**Resposta (201 Created):**
```json
{
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "maria@example.com",
      "first_name": "Maria Silva",
      "role": "USER",
      "accepted_terms_at": "2026-05-21T23:59:00Z",
      "profile": { "birth_date": null, "biological_sex": null, "height_cm": null }
    }
  },
  "error": null,
  "meta": {}
}
```

### 2. Login com credenciais

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria@example.com",
    "password": "SecurePass123"
  }'
```

**Resposta (200 OK):** mesmo formato acima, retornando novos tokens.

### 3. Obter dados do usuário autenticado

Guarde o `access` token e use:

```bash
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Resposta (200 OK):**
```json
{
  "data": {
    "id": 1,
    "email": "maria@example.com",
    "first_name": "Maria Silva",
    "role": "USER",
    "accepted_terms_at": "2026-05-21T23:59:00Z",
    "profile": { "birth_date": null, "biological_sex": null, "height_cm": null }
  },
  "error": null,
  "meta": {}
}
```

### 4. Atualizar perfil do usuário

```bash
curl -X PATCH http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Maria Silva Santos",
    "profile": {
      "birth_date": "1990-05-15",
      "biological_sex": "F",
      "height_cm": 165
    }
  }'
```

**Resposta (200 OK):** retorna dados atualizados.

### 5. Renovar access token

Guarde também o `refresh` token:

```bash
REFRESH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH_TOKEN\"}"
```

**Resposta (200 OK):**
```json
{
  "data": { "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...(novo)" },
  "error": null,
  "meta": {}
}
```

### 6. Testes de erro — Exemplos

**Senha fraca:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "weak", "name": "User", "accept_terms": true}'
```
→ **400** — "Senha deve ter ≥ 8 chars, com letra e dígito."

**Email duplicado:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "maria@example.com", "password": "SecurePass123", "name": "Outra Maria", "accept_terms": true}'
```
→ **400** — "E-mail já cadastrado."

**Sem aceitar termos:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123", "name": "User", "accept_terms": false}'
```
→ **400** — "Aceite dos termos é obrigatório."

**Sem token (acesso negado):**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me
```
→ **401** — "Authentication credentials were not provided."

**Token inválido:**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid-token"
```
→ **401** — "Invalid token."

### 7. Health check

```bash
curl http://localhost:8000/health
```

**Resposta:**
```json
{
  "status": "ok",
  "db": "ok",
  "vector_store": "not_configured",
  "version": "0.1.0"
}
```

---

## 2026-05-19 — Epic 1 (Foundation) Completo ✓

### O que foi desenvolvido
Epic 1 foi concluído com todas as 3 stories:

**Story 1.1 — Estrutura e settings**
- ✅ Reorganização de `config/settings.py` com `_required()` para fail-fast em envs obrigatórias
- ✅ Criação da estrutura de apps (`apps/common`, `apps/accounts`, `apps.health_logs`, etc.)
- ✅ Implementação de `apps/common/`:
  - `exceptions.py` com `AppError`, `GuardrailBlockedError`, `LLMProviderError`, `envelope_exception_handler`
  - `renderers.py` com `EnvelopeJSONRenderer`
  - `pagination.py` com `DefaultPagination`
  - `middleware.py` com `RequestIDMiddleware`
- ✅ Atualização de `config/urls.py` com rotas para todos os apps
- ✅ Atualização de `requirements.txt` com todas as dependências (LangChain, ChromaDB, etc.)

**Story 1.2 — Healthcheck**
- ✅ Endpoint `GET /health` (sem autenticação) que valida Postgres
- ✅ Implementado em `apps/common/views.py` e `apps/common/health_urls.py`
- ✅ Retorna 200 com status quando DB está ok, 503 quando fora

**Story 1.3 — CI**
- ✅ `.gitlab-ci.yml` com stages `lint` (pre-commit) e `test` (pytest)
- ✅ Configuração de variáveis de ambiente para CI
- ✅ CI verde no MR

### Estado de Pronto para E2
- `python manage.py runserver` sobe sem erros
- Resposta de qualquer rota DRF segue envelope `{ data, error, meta }`
- `pre-commit run --all-files` verde
- Próximo: Story 2.1 (geração de tokens JWT)

---

## 2026-05-14 — Stack local conectado

### Problema resolvido
O servidor Django falhava ao iniciar com `OperationalError` porque o PostgreSQL não estava rodando localmente. O banco roda em container Docker, mas os containers estavam parados.

**Solução:** iniciar o serviço `postgres` do devcontainer compose:

```bash
docker network create mediclaw-dev-network 2>/dev/null || true
docker compose -f .devcontainer/docker-compose.yml up postgres -d
```

### Estado atual do stack

| Camada     | URL                          | Tecnologia                        |
|------------|------------------------------|-----------------------------------|
| Backend    | http://localhost:8000        | Django + DRF, uv, Python 3.12     |
| Banco      | localhost:25432              | PostgreSQL 16 (container Docker)  |
| Frontend   | http://localhost:3000        | Next.js + Chakra UI + axios       |

### Endpoints disponíveis no backend

- `GET  /api/health/` — health check
- `POST /api/token/` — obter par de tokens JWT
- `POST /api/token/refresh/` — renovar access token
- `GET  /admin/` — painel admin do Django

### Configuração de ambiente

**Backend** (`.env`):
- `DB_HOST=localhost`, `DB_PORT=25432` → aponta para o container Postgres publicado pelo compose
- Dentro do devcontainer: `DB_HOST=postgres`, `DB_PORT=5432` (DNS interno do Compose)

**Frontend** (`.env.local`):
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/`
- Instância axios exportada de `@/lib/api` usa essa variável como `baseURL`

# Análise de Código — MediClaw (Backend Django)

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO (extraído do código) | 🟡 INFERIDO | 🔴 LACUNA
> Artefato transversal — os módulos são adicionados sequencialmente conforme a escavação avança.

---

## Módulo: accounts

**Caminho:** `django-api/apps/accounts/`
**Propósito:** Usuários, perfis e autenticação JWT. Define o modelo custom de usuário (`AUTH_USER_MODEL = "accounts.User"`), cadastro, login, gestão do próprio perfil e criação admin de usuários.

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `register(request)` | views.py:21 | POST | 201 `{access, refresh, user}` |
| `login(request)` | views.py:39 | POST | 200 `{access, refresh, user}` |
| `admin_create_user(request)` | views.py:58 | POST | 201 `UserSerializer` |
| `me(request)` | views.py:66 | GET/PATCH/DELETE | 200 ou 204 |
| `persist_user_name(user_id, name)` | services/persist.py:9 | `int`, `str` | `{"first_name": str}` |
| `UserManager.create_user(email, password, **extra)` | models.py:6 | `str`, `str`, kwargs | `User` |
| `UserManager.create_superuser(email, password, **extra)` | models.py:15 | `str`, `str`, kwargs | `User` |
| `ensure_welcome_conversation(user)` | conversations/services/welcome.py:23 | `User` | `Conversation \| None` |

**Fluxos principais** (detalhe em `flowcharts/accounts.md`):

- **Register** → valida `RegisterSerializer` → `create_user` + `accepted_terms_at=now` → gera `RefreshToken` → `record("USER_REGISTERED")` → cria conversa de boas-vindas → 201 com access/refresh/user.
- **Login** → email em minúsculas → `authenticate` → checa `is_active` → `AppError INVALID_CREDENTIALS` (401) em falha → gera tokens → `record("LOGIN")` → 200.
- **Me PATCH** → `MeUpdateSerializer` (partial) → atualiza apenas campos enviados via `update_fields`.
- **Me DELETE** → `user.delete()` → 204 (cascade de dados sensíveis — LGPD Art. 11).

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Política de senha | `^(?=.*[A-Za-z])(?=.*\d).{8,}$` — mín. 8 chars, com letra e dígito | serializers.py:6 | 🟢 |
| Normalização de email | Sempre minúsculo no cadastro e login | serializers.py:30; views.py:40 | 🟢 |
| Unicidade de email | Case-insensitive (`iexact`), no cadastro e no `PATCH me` (exclui o próprio pk) | serializers.py:28, 58 | 🟢 |
| Login sigiloso | Falha de credencial OU usuário inativo → mesmo código `INVALID_CREDENTIALS` 401 | views.py:43 | 🟢 |
| Consentimento LGPD | `accept_terms` obrigatório; grava `accepted_terms_at = now()` | serializers.py:22; views (via serializer) | 🟢 |
| Atualização parcial | `me PATCH` usa `update_fields` — só persiste campos presentes | views.py:79-87 | 🟢 |
| Nome via chat | `persist_user_name`: trim, 2–120 chars, `update_fields=["first_name"]` | services/persist.py:9 | 🟢 |
| Boas-vindas idempotente | Não recria conversa "Bem-vindo" se já existe; pula para `ADMIN` | conversations/services/welcome.py:29 | 🟢 |

### 3. Estruturas de dados

- **Entidade:** `User` (custom, estende `AbstractUser`) — ver `data-dictionary.md`.
- **Relacionamentos (inbound, cascade confirmado):** o cascade de `User.delete()` flui por `Patient.doctor` (patients/models.py:11) e `Conversation.doctor` (conversations/models.py:15); logs biométricos (health_logs) penduram no `Patient` com `on_delete=CASCADE`. `Conversation.patient` usa `SET_NULL`. Rede completa em `data-dictionary.md`. 🟢

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `AUTH_USER_MODEL` | `accounts.User` | config/settings.py:113 |
| `USERNAME_FIELD` | `email` (`REQUIRED_FIELDS = []`) | models.py:29-30 |
| Roles | `USER` (padrão), `ADMIN` | models.py:23 |
| JWT access | 30 min (env `ACCESS_TOKEN_MINUTES`) | settings.py:133 |
| JWT refresh | 1 dia (env `REFRESH_TOKEN_DAYS`) | settings.py:136 |
| Header auth | `Authorization: Bearer <token>` | settings.py:139 |
| Throttling global | anon `30/min`, user `60/min` | settings.py:127 |
| Renderer padrão | `EnvelopeJSONRenderer` | settings.py:120 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | `AllowAny` | Cadastro + access/refresh |
| POST | `/api/v1/auth/login/` | `AllowAny` | Login + access/refresh |
| POST | `/api/v1/auth/refresh/` | (JWT refresh) | Renova access token (`TokenRefreshView`) |
| GET | `/api/v1/auth/me/` | `IsAuthenticated` | Perfil do usuário logado |
| PATCH | `/api/v1/auth/me/` | `IsAuthenticated` | Atualiza `first_name`/`email` |
| DELETE | `/api/v1/auth/me/` | `IsAuthenticated` | Deleta conta (cascade) → 204 |
| POST | `/api/v1/admin/users/` | `IsAdminRole` | Admin cria usuário (view em `accounts`, rota em `audit/urls.py`) |

### 6. Dependências

- `rest_framework_simplejwt` — `RefreshToken`, `TokenRefreshView`, `JWTAuthentication`
- `apps.audit.services.log.record` — auditoria (stub, não persiste)
- `apps.common.exceptions.AppError` — erro de negócio com `code`
- `apps.common.permissions.IsAdminRole` — role `ADMIN`
- `apps.conversations.services.welcome.ensure_welcome_conversation` — onboarding
- `apps.ai_engine.prompts.DISCLAIMER` — transitivo, injetado na mensagem de boas-vindas

### 7. Achados

- 🟢 `admin_create_user` está roteado em **`/api/v1/admin/users/`** (apps/audit/urls.py:7), fora do namespace de auth — intencional (admin).
- 🔴 `apps/audit/services/log.py::record` é um stub `pass` — `register`/`login` o chamam mas nada é persistido no MVP. Expandir no Epic 3.
- 🟢 `record` recebe apenas eventos e usuário (metadados), sem conteúdo de mensagem — aderente à política de não logar PII.
- 🟢 `username` é `CharField(blank=True)` — campo herdado do `AbstractUser`, não usado como identificador (login via email).
- 🟢 Cobertura de testes: `tests/accounts/test_auth.py` (register, login, me). Sem teste dedicado para `admin_create_user` nem `persist_user_name`.

---

## Módulo: patients

**Caminho:** `django-api/apps/patients/`
**Propósito:** CRUD de pacientes por médico, com anotações agregadas (contagem de conversas, última atividade, último peso) e serviços de deduplicação via captura no chat.

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `list_patients(request)` | views.py:38 | GET | `{results, count, next}` (paginação manual, page size 20) |
| `patient_detail(request, patient_id)` | views.py:56 | GET/PATCH/DELETE | 200 serializer / 204 |
| `_annotate_patients(qs)` | views.py:16 | `QuerySet[Patient]` | `QuerySet` anotado |
| `ensure_or_create_patient(conversation_id, doctor_id, first_name)` | services/patient.py:10 | `int, int, str` | `Patient` |
| `resolve_patient_dob(conversation_id, doctor_id, birth_date)` | services/patient.py:45 | `int, int, date` | `Patient \| None` |

**Fluxos principais** (detalhe em `flowcharts/patients.md`):

- **List** → filtra por `doctor=request.user` → anota `conversation_count`, `last_seen_at`, `latest_weight_kg` → paginação manual (page size 20) com `next` em URL query.
- **Detail GET** → busca por pk **dentro do escopo do médico** (senão `NOT_FOUND` 404) → retorna `PatientDetailSerializer` com logs + conversas.
- **Detail PATCH** → `PatientListSerializer` partial (edita nome/DOB/sexo/altura).
- **Detail DELETE** → `patient.delete()` → 204.
- **Chat (services)** → conversa cria seu próprio `Patient` tentativo (dedup por nome+DOB apenas quando DOB é conhecido).

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Escopo por médico | Toda query filtra `doctor=request.user`; pk fora do escopo → `NOT_FOUND` 404 | views.py:41, 58 | 🟢 |
| Dedup condicional | `UniqueConstraint(doctor, first_name, birth_date)` **somente quando** `birth_date` preenchido (partial) | models.py:24-30 | 🟢 |
| Anotações agregadas | `conversation_count` (conversas não deletadas), `last_seen_at` (max updated_at), `latest_weight_kg` (subquery top-1 por `measured_at`) | views.py:16-33 | 🟢 |
| Paciente por conversa | Cada conversa gera `Patient` próprio (tentativo) até o DOB ser capturado | services/patient.py:30 | 🟢 |
| Merge ao capturar DOB | Mesmo nome+DOB do médico → re-vincula conversa e **deleta tentativo** se não tiver dados | services/patient.py:59-89 | 🟢 |
| Título da conversa | Atualizado para o nome do paciente (`[:120]`) ao vincular | services/patient.py:35 | 🟢 |
| Logging | `logger.debug("patient_created"/"patient_merged")` com IDs, sem PII | services/patient.py:37, 83 | 🟢 |

### 3. Estruturas de dados

- **Entidade:** `Patient` — ver `data-dictionary.md`.
- **Relacionamentos:** `doctor` (User, CASCADE, `related_name="patients"`), `conversations` (1..N, `SET_NULL` no Patient), logs biométricos (1..N, CASCADE).

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `SEX_CHOICES` | `M`, `F`, `OTHER` | models.py:5 |
| Paginação | Manual, `PAGE_SIZE = 20`, parâmetro `?page=` | views.py:13, 39 |
| Índices | `(doctor, first_name)`, `(doctor, -created_at)` | models.py:31-34 |
| Ordenação | `-created_at` (padrão do modelo) | models.py:35 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/api/v1/patients/` | `IsAuthenticated` | Lista pacientes do médico (paginado) |
| GET | `/api/v1/patients/<id>/` | `IsAuthenticated` | Detalhe + logs biométricos + conversas |
| PATCH | `/api/v1/patients/<id>/` | `IsAuthenticated` | Atualiza dados básicos |
| DELETE | `/api/v1/patients/<id>/` | `IsAuthenticated` | Deleta paciente → 204 |

### 6. Dependências

- `apps.health_logs.models.WeightLog` (anotação `latest_weight_kg`)
- `apps.conversations.models.Conversation` (relação paciente/conversa)
- `apps.common.exceptions.AppError`
- `apps.common.logging_config.get_logger`

### 7. Achados

- 🟢 CRUD de pacientes é **read-only em criação** via HTTP: não há endpoint POST de paciente — criação vem do chat (services) ou de logs. `list_patients`/`patient_detail` só listam/atualizam/deletam.
- 🟢 Paginação manual (`offset/limit` via slicing) em vez do `DefaultPagination` global — inconsistência menor de padrão com o resto da API (renderer usa envelope, mas este endpoint retorna `{results, count, next}` direto). Registrar para o Architect.
- 🟢 Anotação `latest_weight_kg` usa `Subquery` com `OuterRef` — sem N+1 na listagem.
- 🟡 A busca de `latest_weight_kg` não filtra por `deleted_at` (não existe soft-delete em WeightLog) — sem impacto hoje.
- 🟢 Sem testes dedicados para `patients` em `tests/` (apenas cobertura via fluxos de chat e health_logs).

---

## Módulo: health_logs

**Caminho:** `django-api/apps/health_logs/`
**Propósito:** Registro e agregação de logs biométricos (peso, sono, atividade, nutrição) por paciente, via REST (Viewsets) e via captura automática no chat (services de persistência).

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `WeightLogViewSet` / `SleepLogViewSet` / `ActivityLogViewSet` / `NutritionNoteViewSet` | views.py:55-84 | Router (GET/POST/DELETE) | ModelViewSet |
| `health_summary(request)` | views.py:87 | GET | resumo agregado |
| `summarize(patient_id, window_days=7)` | services/aggregate.py:9 | `int, int` | `dict` agregado |
| `persist_weight_log(patient_id, data)` | services/persist.py:21 | `int, dict` | `dict` (id + valores) |
| `persist_sleep_log(patient_id, data)` | services/persist.py:39 | `int, dict` | `dict` |
| `persist_activity_log(patient_id, data)` | services/persist.py:62 | `int, dict` | `dict` |
| `persist_nutrition_note(patient_id, data)` | services/persist.py:87 | `int, dict` | `dict` |

**Fluxos principais** (detalhe em `flowcharts/health_logs.md`):

- **REST (Viewsets)** → mixin `_PatientQuerysetMixin` exige `patient_id` (query param) e valida ownership → filtra por intervalo `from`/`to` no campo timestamp do tipo → `perform_create` valida `patient_id` no body e ownership.
- **Summary** → `patient_id` obrigatório (400 se ausente) → `window` aceito `7` ou `30` (padrão 7, inválidos caem para 7) → `summarize()` agrega sono (avg), peso (último + tendência), atividade (sum) e últimas 3 notas de nutrição.
- **Persistência via chat** → valida intervalo/regras e cria registro com `patient_id`.

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Peso plausível | `20 ≤ value_kg ≤ 400` (HTTP e via chat) | serializers.py:14; persist.py:23 | 🟢 |
| Timestamp futuro | Rejeitado (`measured_at`/`started_at`/`performed_at`/`logged_at`) | serializers.py:21; persist.py:15 | 🟢 |
| Qualidade do sono | `1 ≤ quality_score ≤ 10`; default `5` via chat | serializers.py:32; persist.py:11 | 🟢 |
| Duração do sono | `0 < duration_hours ≤ 24` (validação via chat; REST não valida faixa) | persist.py:41 | 🟢 |
| Duração da atividade | `duration_min ≥ 1`; `type` obrigatório, truncado a 40 chars via chat | serializers.py:45; persist.py:64 | 🟢 |
| Nota de nutrição | mínimo 10 e máximo 1000 chars (via chat); REST só max 1000 | persist.py:89; serializers.py:57 | 🟢 |
| Ownership | Logs sempre filtrados por `patient_id` + `doctor=request.user`; acesso a outro paciente → 404 | views.py:19-24, 34 | 🟢 |
| Sem PATCH/PUT | `http_method_names = ["get","post","delete"]` — logs são imutáveis (append-only) | views.py:60 | 🟢 |
| Janela de resumo | `window` ∈ {7, 30}; fora → 7 | views.py:93-95 | 🟢 |
| Tendência de peso | `latest_weight − first_weight` (dentro da janela), `None` se faltar algum | aggregate.py:16-32 | 🟢 |
| Notas recentes | Top-3 por `-logged_at`, sem janela de tempo | aggregate.py:41-45 | 🟢 |

### 3. Estruturas de dados

- **Entidades:** `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` — ver `data-dictionary.md`. Todas apontam para `Patient` com CASCADE.

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `DEFAULT_SLEEP_QUALITY` | `5` | persist.py:11 |
| `MIN_NUTRITION_NOTE_LEN` | `10` | persist.py:12 |
| Janelas de summary | `7` e `30` dias | views.py:93 |
| Índices | `(patient, -<timestamp>)` por entidade | models.py |
| Ordenação | por timestamp desc por entidade | models.py |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET/POST/DELETE | `/api/v1/health/weight/`, `.../sleep/`, `.../activity/`, `.../nutrition/` | `IsAuthenticated` | CRUD parcial por tipo de log (`patient_id` obrigatório) |
| GET | `/api/v1/health/summary/?patient_id=&window=` | `IsAuthenticated` | Resumo agregado 7/30 dias |

> DELETE: `DeleteModelMixin` do ViewSet usa o pk do log; a queryset já está restrita ao paciente autenticado → log de outro médico retorna 404 (testado). 🟢

### 6. Dependências

- `apps.patients.models.Patient` (ownership + FK)
- `apps.common.exceptions.AppError`
- **Callers dos serviços de persistência:** `apps.ai_engine.services.user_data_capture` (chat)
- **Caller de `summarize`:** `apps.ai_engine.skills.health_summary` (skill do LLM)

### 7. Achados

- 🟢 Logs são **append-only** (sem PATCH/PUT) — histórico biométrico imutável.
- 🟢 Validações duplicadas entre REST (serializers) e chat (services.persist) com regras levemente divergentes: duração do sono `0 < h ≤ 24` e nota mínima de nutrição `10` existem **apenas** na via chat. Padrão: services não reusam os serializers. Registrar para o Architect.
- 🟢 `summarize` executa 5 queries separadas (uma por agregação) — sem risco de N+1 mas 1+ round-trips. Oportunidade de otimização não-crítica.
- 🟢 `weight_trend_kg` compara `latest_weight` (sem janela) com `first_weight` (na janela) — comportamento assimétrico intencional? Registrar como 🟡 para validação.
- 🟢 Testes: `tests/health_logs/test_summary.py` cobre summary + validação de peso + isolamento entre pacientes.

---

## Módulo: conversations

**Caminho:** `django-api/apps/conversations/`
**Propósito:** Histórico de chat com a IA. CRUD de conversas (soft-delete), envio de mensagens (REST e streaming SSE via EventSource), serialização manual e conversa de boas-vindas. A geração de resposta é delegada a `apps.ai_engine.orchestrator` — este módulo é a camada de transporte/HTTP.

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `list_create(request)` | views.py:57 | GET/POST | 200 `{results, count, next}` / 201 conv |
| `detail(request, conv_id)` | views.py:79 | GET/DELETE | 200 `{conversation, messages}` / 204 |
| `post_message(request, conv_id)` | views.py:103 | POST | 201 `MessageSerializer` |
| `stream(request, conv_id)` | views.py:120 | GET (view Django pura) | `StreamingHttpResponse` SSE |
| `_serialize_patient(patient)` | views.py:29 | `Patient \| None` | `dict \| None` |
| `_serialize_conversation(conv)` | views.py:35 | `Conversation` | `dict` |
| `_serialize_message(msg)` | views.py:45 | `Message` | `dict` |
| `send_message(user, conversation, content)` | services/chat.py:10 | `User, Conversation, str` | `Message` (assistente) |
| `ensure_welcome_conversation(user)` | services/welcome.py:23 | `User` | `Conversation \| None` |

**Fluxos principais** (detalhe em `flowcharts/conversations.md`):

- **List** → filtra `doctor=request.user` + `select_related("patient")` → paginação manual (page size 20) com `next` em query string → serialização manual (helpers, não serializers).
- **Create** → `Conversation.objects.create(doctor=request.user, title="Nova conversa")` → 201.
- **Detail GET** → `get(pk, doctor=request.user)` → 404 `NOT_FOUND` se não for do médico → retorna conversa + todas as mensagens.
- **Detail DELETE** → soft delete: `deleted_at = now()` + `save(update_fields=["deleted_at"])` → 204. Linha some da query padrão (`ActiveConversationManager`), mas persiste em `all_objects`.
- **Post message** → `ChatThrottle` (10/min) → ownership 404 → `CreateMessageInput` valida (1–4000 chars) → `send_message`.
- **Stream** → **view Django pura** (sem `@api_view`), autenticação via `?token=<AccessToken>` no query string (EventSource não envia headers) → valida token, conv, prompt não vazio, limite de mensagens → persiste mensagem USER → seta título (`prompt[:80]` se vazio/"Nova conversa") → gera `event_stream()` que itera `orchestrator.generate_stream`.

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Ownership por médico | Toda query filtra `doctor=request.user`; conversa de outro → 404 `NOT_FOUND` | views.py:66, 84, 109, 154; chat.py:11 | 🟢 |
| Soft delete | `deleted_at` timestamp; manager `ActiveConversationManager` exclui; `all_objects` inclui | models.py:5-10, 30-31 | 🟢 |
| Limite de mensagens | `conv.messages.count() >= MAX_MESSAGES` → 400. **Divergência:** views.py:22 hardcoda `50`; chat.py:7 lê env `MAX_MESSAGES_PER_CONVERSATION` | views.py:22, 177; chat.py:7 | 🟢 |
| Código do limite | Erro lançado é `CONVERSATION_FULL` (views.py:181, chat.py:14) — **não** é o `CONVERSATION_LIMIT_REACHED` documentado no PROJECT-CONTEXT.md | views.py:181; chat.py:14 | 🟢 |
| Título automático | Primeiro prompt define título `prompt[:80]` (se título vazio ou "Nova conversa") | views.py:190-192 | 🟢 |
| Persistência do turno | Mensagem USER salva **antes** da chamada LLM; ASSISTANT salva no evento `done` com metadados (citações, onboarding, data_capture) | views.py:189, 237-244; chat.py:19 | 🟢 |
| Guardrail via stream | `blocked=True` → content = `canned_reply + DISCLAIMER`, `tokens_used=0`, flag salva | orchestrator (evento `done`) | 🟢 |
| Metadata JSON | `Message.metadata` guarda `citations`, `onboarding_mode`, `missing_basics`, `data_capture` | views.py:230-236; chat.py:28-35 | 🟢 |
| Streaming SSE | Cada evento → `data: {json}\n\n`; headers `Cache-Control: no-cache` e `X-Accel-Buffering: no` | views.py:262-264 | 🟢 |
| Boas-vindas estática | Sem LLM: mensagem ASSISTANT fixa (com `DISCLAIMER`), `tokens_used=0`, flag `welcome: true`; idempotente; pulada para `ADMIN` | services/welcome.py:10-50 | 🟢 |
| `transaction.atomic` | Criação da mensagem USER dentro de transação (não-blocking; LLM fora da transação) | chat.py:18 | 🟢 |

### 3. Estruturas de dados

- **Entidades:** `Conversation` (com soft-delete) e `Message` — ver `data-dictionary.md`.
- **Relacionamentos:** `Conversation.doctor` (User, CASCADE, `related_name="conversations"`), `Conversation.patient` (Patient, `SET_NULL` null=True), `Message.conversation` (Conversation, CASCADE, `related_name="messages"`).

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `PAGE_SIZE` | 20 (paginação manual) | views.py:21 |
| `MAX_MESSAGES` | 50 (hardcoded em views) / env `MAX_MESSAGES_PER_CONVERSATION` (service) | views.py:22; chat.py:7 |
| Throttle chat | `ChatThrottle` scope `"chat"` → `10/min` | views.py:25-27; settings.py:127 |
| `Message.ROLE_CHOICES` | `USER`, `ASSISTANT`, `SYSTEM` | models.py:42 |
| `WELCOME_CONVERSATION_TITLE` | `"Bem-vindo"` | services/welcome.py:7 |
| `WELCOME_METADATA_FLAG` | `"welcome"` | services/welcome.py:8 |
| Índices | `(doctor, -updated_at)`, `(patient, -updated_at)`, `(conversation, created_at)` | models.py:36-38, 56-58 |
| Ordenação | Conversation `-updated_at`; Message `created_at` | models.py:34, 54 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET/POST | `/api/v1/conversations/` | `IsAuthenticated` | Lista (paginada) / cria conversa |
| GET/DELETE | `/api/v1/conversations/<id>/` | `IsAuthenticated` | Detalhe + mensagens / soft-delete → 204 |
| POST | `/api/v1/conversations/<id>/messages/` | `IsAuthenticated` + `ChatThrottle` | Envia mensagem e retorna resposta (bloqueante) |
| GET | `/api/v1/conversations/<id>/stream/?token=&prompt=` | AccessToken via query (view pura) | Streaming SSE com a resposta da IA |

### 6. Dependências

- `apps.ai_engine.orchestrator` — `generate` (rest) e `generate_stream` (SSE)
- `apps.ai_engine.prompts.DISCLAIMER` — injetado na boas-vindas (welcome.py)
- `apps.common.exceptions.AppError` — erros de negócio (NOT_FOUND, FORBIDDEN, CONVERSATION_FULL)
- `apps.common.logging_config.get_logger` — structlog (`logger.warning("stream_error")`, `logger.exception("stream_unexpected_error")`, metadados sem PII)
- `rest_framework_simplejwt` — `AccessToken` para auth do stream via query param
- **Consumidores:** `apps.accounts.services` (boas-vindas no register), `apps.patients.services.patient` (atualiza título/vincula paciente), `apps.ai_engine.services.user_data_capture` (lê mensagens para extrair dados)

### 7. Achados

- 🟢 O endpoint `stream` é **view Django pura** (sem `@api_view`/`permission_classes`/`throttle_classes`): ignora renderer, exception handler e throttle do DRF. Autenticação via `?token=` (AccessToken no query string) — fica exposta em logs de proxy/access log. Necessário para EventSource, mas registrar para o Architect.
- 🟢 `except (TokenError, Exception)` em views.py:142 — a cláusula `Exception` é catch-all (inclui `TokenError`) e engole também erros de programação (ex.: `User.DoesNotExist`) mascarando bugs. `User.DoesNotExist` de um token válido com user_id inexistente cai aqui como "Token inválido".
- 🟢 **Divergência de constante:** `MAX_MESSAGES` hardcoded `50` em views.py vs env `MAX_MESSAGES_PER_CONVERSATION` em chat.py. Se o env mudar, `messages/` respeita o env mas `stream/` continua com 50.
- 🟢 **Divergência de código de erro:** limite dispara `CONVERSATION_FULL`, mas o PROJECT-CONTEXT.md documenta `CONVERSATION_LIMIT_REACHED`. Cliente React precisa saber qual tratar.
- 🟢 **Retenção de 90 dias não implementada:** `CONVERSATION_RETENTION_DAYS` documentado no PROJECT-CONTEXT.md, mas não há management command/job de limpeza de conversas/mensagens antigas em nenhum app. 🔴 LACUNA — requisito LGPD pendente.
- 🟢 **Sem throttle no stream:** só `post_message` tem `ChatThrottle` (10/min). Como o frontend usa `stream/` como caminho principal, o limite de 10/min não se aplica ao caminho mais usado.
- 🟢 **Serializers subutilizados:** `ConversationSerializer`, `ConversationDetailSerializer` e `MessageSerializer` existem, mas list/detail/stream serializam manualmente via helpers `_serialize_*`. Só `post_message` usa `MessageSerializer`. Duplicação de contrato de saída.
- 🟢 **Soft delete sem purga:** conversas deletadas persistem com `deleted_at`; mensagens não têm soft-delete e não há job de expurgo — dados acumulam indefinidamente (agravado pela retenção ausente).
- 🟢 `is_first = conv.messages.count() == 0` calculado duas vezes no mesmo request (views.py:188 e chat.py:16) — redundância menor.
- 🟢 Testes: `tests/conversations/test_conversations.py` (CRUD, ownership 404, soft-delete, stream com token ausente/vazio/orchestrator mockado, inclusão de histórico) e `test_welcome.py` (mensagem, idempotência, skip ADMIN, integração via register). Boa cobertura.

---

## Módulo: ai_engine

**Caminho:** `django-api/apps/ai_engine/`
**Propósito:** Orquestração da camada de IA. Monta prompts (system + histórico + RAG + resumo de saúde), aplica guardrails de entrada/saída, captura automaticamente dados do paciente a partir da mensagem (regex + LLM) e delega a geração ao provider configurado (OpenAI/Gemini). Inclui skills auxiliares (IMC, conversão de unidades, prontidão do perfil). **Sem endpoints próprios** — `urls.py` vazio; é consumido pela camada `conversations`.

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `generate(user_id, conversation_id, query, *, is_first_message=False)` | orchestrator.py:183 | `int, int, str, bool` | `GenerateResult` |
| `generate_stream(user_id, conversation_id, query, *, is_first_message=False)` | orchestrator.py:261 | `int, int, str, bool` | `Iterator[dict]` (eventos SSE) |
| `_resolve_messages(...)` | orchestrator.py:158 | `patient_id, conversation_id, query, is_first_message, capture` | `tuple[messages, citations, onboarding_mode, missing_basics]` |
| `_build_messages(...)` | orchestrator.py:115 | `patient_id, conversation_id, query, readiness, capture` | `tuple[...]` |
| `_build_onboarding_focus_messages(...)` | orchestrator.py:100 | `conversation_id, query, readiness, capture` | `list[dict]` |
| `_load_history(conversation_id)` | orchestrator.py:78 | `int` | `list[dict]` (últimas `HISTORY_WINDOW` msgs) |
| `_history_with_query(conversation_id, query)` | orchestrator.py:89 | `int, str` | `list[dict]` |
| `check_input(text)` | guardrails.py:135 | `str` | `GuardrailResult` |
| `check_output(text)` | guardrails.py:147 | `str` | `GuardrailResult` |
| `get_provider()` | providers/__init__.py:4 | — | `OpenAIProvider \| GeminiProvider` |
| `OpenAIProvider.stream / complete / complete_json` | providers/openai_provider.py:16,31,42 | `messages, max_tokens` | `Iterator[str]` / `(str, int)` / `str` |
| `GeminiProvider.stream / complete / complete_json` | providers/gemini_provider.py:42,55,69 | `messages, max_tokens` | idem (via `_build`/`_config`) |
| `capture_from_message(conversation_id, doctor_id, text)` | services/user_data_capture.py:26 | `int, int, str` | `CaptureResult` |
| `parse_rules(text)` | services/capture_rules.py:108 | `str` | `ExtractedUserData` (regex) |
| `has_actionable_data(data)` | services/capture_rules.py:175 | `ExtractedUserData` | `bool` |
| `message_likely_has_health_data(text)` | services/capture_rules.py:192 | `str` | `bool` |
| `extract_with_llm(text)` | services/data_extraction_llm.py:58 | `str` | `ExtractedUserData \| None` |
| `merge_extracted(primary, secondary)` | services/data_extraction_llm.py:75 | `ExtractedUserData, ExtractedUserData` | `ExtractedUserData` (rules win) |
| `calculate_bmi(weight_kg, height_cm)` | skills/bmi.py:9 | `float, float` | `dict {bmi, category}` |
| `convert_units(value, from_unit, to_unit)` | skills/unit_convert.py:15 | `float, str, str` | `dict {value, unit}` |
| `health_summary(patient_id, window=7)` | skills/health_summary.py:4 | `int \| None, int` | `dict` (delega a `aggregate.summarize`) |
| `get_user_readiness(patient_id)` | skills/user_readiness.py:42 | `int \| None` | `UserReadiness` |

**Fluxos principais** (detalhe em `flowcharts/ai_engine.md`):

- **`generate` (REST, não-streaming)** → `check_input(query)` (urgency→diagnosis→prescription→gibberish). Se bloqueado: resposta canônica + `DISCLAIMER`, `tokens_used=0`, `blocked=True`, `record("GUARDRAIL_BLOCKED")`. Se liberado: `capture_from_message` (extrai e persiste dados do paciente) → `_resolve_messages` (escolhe template de prompt) → `provider.complete` → `check_output(content)`. Se output bloqueado: resposta canônica + disclaimer. Senão: garante `DISCLAIMER` no fim → `record("MESSAGE_SENT")` com `tokens_used`/`latency_ms`.
- **`generate_stream` (SSE)** → mesma sequência, mas emite eventos `{type: citation}` (um por chunk RAG), `{type: token}` (por token), e `{type: done}` ao final com metadados (`onboarding_mode`, `missing_basics`, `data_capture`, `patient_id`, `patient_first_name`). Erros do provider viram `{type: error, code: LLM_PROVIDER_ERROR}`. Output bloqueado emite texto de supressão e `done` com `blocked=True, tokens_used=0`. `tokens_used` no streaming = `len(text.split())` (palavras, não tokens reais).
- **Onboarding** → `get_user_readiness(patient_id)`. Se `is_complete`: prompt normal. Se incompleto **e primeira mensagem**: modo `focus` (só orienta registro dos dados faltantes, não responde perguntas clínicas). Se incompleto e não-primeira: modo `soft` (responde + apêndice lembrando dados faltantes).
- **Captura de dados** → `message_likely_has_health_data` (keywords, ≥8 chars) → `parse_rules` (regex) → `_should_call_llm` (env `DATA_CAPTURE_LLM`, texto ≥5 chars ou regras acharam algo) → `extract_with_llm` → `merge_extracted` (regras vencem; LLM só preenche gaps) → `has_actionable_data` → `_ensure_patient` (cria/resolve Patient por nome e DOB) → `_persist_health_data` (profile, weight, sleep, activity, nutrition) → `get_user_readiness` atualiza `still_missing`.

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Ordem do guardrail de entrada | `URGENCY_PATTERNS` → `DIAGNOSIS_PATTERNS` → `PRESCRIPTION_PATTERNS` → `_is_gibberish`; primeiro match vence | guardrails.py:136-143 | 🟢 |
| Respostas canônicas | Cada bloqueio tem `canned_reply` próprio (URGENCY_REPLY, DIAGNOSIS_REPLY, PRESCRIPTION_REPLY, GIBBERISH_REPLY) + `DISCLAIMER` | guardrails.py:35-50 | 🟢 |
| Guardrail de saída | `FORBIDDEN_OUTPUT_PATTERNS` (ex.: "você tem câncer", "tome X mg", "diagnóstico é") → bloqueia resposta | guardrails.py:71-77, 147 | 🟢 |
| Detecção de gibberish | Normaliza NFKD→ASCII→lower; palavra plausível se ≥3 chars, tem vogal, sem 6+ consoantes seguidas; texto de ≥3 palavras com <34% plausíveis → gibberish; repetição `(.)\1{6,}` → gibberish | guardrails.py:84-132 | 🟢 |
| Onboarding focus vs soft | `is_complete` → normal; incompleto+1ª msg → focus; incompleto+não-1ª → soft | orchestrator.py:165-179 | 🟢 |
| Captura rules-first | Regras regex têm precedência sobre LLM; `merge_extracted` só preenche `None`/gap do secundário | data_extraction_llm.py:75 | 🟢 |
| Prontidão mínima | `REQUIRED_PROFILE_FIELDS = (birth_date, biological_sex, height_cm)` + nome + ao menos 1 WeightLog → `is_complete` | skills/user_readiness.py:5, 74 | 🟢 |
| Disclaimer obrigatório | Se a resposta não termina com `DISCLAIMER`, é anexado (REST). No streaming, o disclaimer vem via prompt/instruções | orchestrator.py:241-242; prompts.py | 🟢 |
| Citações RAG | Cada chunk recuperado vira citação `{source, chunk_id}`; injetadas no system prompt com `(fonte: {source})` | orchestrator.py:122-135, 154 | 🟢 |
| Gemini role coalescing | Mensagens consecutivas do mesmo role são concatenadas (Gemini exige alternância) | providers/gemini_provider.py:24-29 | 🟢 |
| IMC | `bmi = round(kg/(m²), 2)`; categorias `<18.5/25/30/35/40` | skills/bmi.py:9-25 | 🟢 |
| Conversão de unidades | Mapa `CONVERSIONS`: kg↔lb, cm↔in, ml↔fl_oz; não suportado → `ValueError` | skills/unit_convert.py:5-19 | 🟢 |
| `patient_created` | Nunca é setado de fato — `_ensure_patient` lê `getattr(result, "_patient_just_created", False)` que não existe em `CaptureResult` → sempre `False` | user_data_capture.py:124 | 🟡 |
| Captura de nome | Regex `(?:meu nome é|me chamo|sou (o\|a)|paciente:)\s+(...)` | capture_rules.py:57-61 | 🟢 |
| Parsing de data | 2-4 dígitos no ano; ano `<100` → `+1900` se `>30` senão `+2000` | capture_rules.py:84-91 | 🟢 |

### 3. Estruturas de dados

- **Entidades ORM:** nenhuma nova — o módulo não define models. Consome `Patient`, `Message`, `Conversation` e logs de `health_logs`.
- **Estruturas em memória** (Pydantic/dataclasses/typing) — detalhe em `data-dictionary.md`: `GenerateResult`, `GuardrailResult`, `UserReadiness`, `CaptureResult`, `ExtractedUserData` + sub-modelos (`ExtractedProfile`, `ExtractedWeight`, `ExtractedSleep`, `ExtractedActivity`, `ExtractedNutrition`), `ChatMessage` (TypedDict), `LLMProvider` (Protocol).

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `HISTORY_WINDOW` | `6` (env) | orchestrator.py:27 |
| `MAX_TOKENS` | `800` (env `MAX_TOKENS_PER_RESPONSE`) | orchestrator.py:28 |
| `LLM_PROVIDER` | `openai` (padrão) \| `gemini` | providers/__init__.py:5 |
| `CHAT_MODEL` | `gpt-4o-mini` (OpenAI) / `gemini-2.0-flash` (Gemini) | openai_provider.py:14; gemini_provider.py:15 |
| `DATA_CAPTURE_LLM` | `true` (env) — habilita extração via LLM | data_extraction_llm.py:47 |
| `RAG_TOP_K` / `RAG_MIN_SCORE` | `5` / `0.75` (env) | orchestrator.py:126-127 |
| `max_tokens` extração | `400` (hardcoded) | data_extraction_llm.py:68 |
| `REQUIRED_PROFILE_FIELDS` | `(birth_date, biological_sex, height_cm)` | skills/user_readiness.py:5 |
| `DISCLAIMER` | Texto fixo de apoio à decisão clínica | prompts.py:57-60 |
| Constantes de prompt | `SYSTEM_PROMPT_TEMPLATE`, `ONBOARDING_FOCUS_TEMPLATE`, `ONBOARDING_SOFT_APPENDIX`, `ONBOARDING_STILL_MISSING_APPENDIX`, `DATA_CAPTURE_SAVED_APPENDIX`, `CITATION_LINE` | prompts.py |
| Regex de captura | `_WEIGHT_KG_RE`, `_HEIGHT_CM_RE`, `_DATE_RE`, `_SEX_RE`, `_SLEEP_HOURS_RE`, `_ACTIVITY_RE`, `_NUTRITION_TRIGGERS`, `_NAME_RE` | capture_rules.py:16-61 |
| `CONVERSIONS` | kg↔lb (2.20462), cm↔in (0.393701), ml↔fl_oz (0.033814) | skills/unit_convert.py:2-12 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| — | — | — | **Nenhum.** `urls.py` vazio. O módulo é camada de serviço; endpoints vivem em `conversations` (`/messages/` e `/stream/`) |

### 6. Dependências

- `apps.rag.retriever.search` — recuperação RAG (top-k, score mínimo)
- `apps.health_logs.services.aggregate.summarize` — resumo agregado (via `skills/health_summary.py`)
- `apps.health_logs.services.persist.*` — `persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note`
- `apps.patients.services.patient` — `ensure_or_create_patient`, `resolve_patient_dob`
- `apps.patients.models.Patient`, `apps.conversations.models.Message/Conversation`
- `apps.audit.services.log.record` — auditoria (stub no MVP)
- `apps.common.exceptions` — `AppError`, `LLMProviderError` (502 no envelope)
- `apps.common.logging_config` — structlog (metadados sem PII)
- Bibliotecas: `openai`, `google.genai`, `pydantic` (v2)
- **Consumidores:** `apps.conversations.views` (`generate`/`generate_stream`), `apps.conversations.services.welcome` (`DISCLAIMER`)

### 7. Achados

- 🟢 **Sem endpoints próprios** — `urls.py` vazio; módulo puramente de serviço, exposto indiretamente via `conversations`.
- 🟢 **Double guardrail:** `check_input` antes e `check_output` depois da geração. No streaming, output bloqueado suprime com texto de segurança e `done` com `blocked=True, tokens_used=0`.
- 🟢 **Captura rules-first com LLM opcional:** `DATA_CAPTURE_LLM=false` desliga a extração via LLM mantendo as regex — bom fallback de custo/privacidade.
- 🟢 **Provider Anthropic documentado mas ausente:** PROJECT-CONTEXT.md prevê OpenAI **ou Anthropic**; o código implementa OpenAI e **Google Gemini** (`GOOGLE_API_KEY`, `gemini-2.0-flash`). Sem classe Anthropic. 🟡 Divergência de spec vs código.
- 🟢 **Uso de `os.getenv` fora de `settings.py`:** orchestrator, providers e data_extraction_llm leem env vars diretamente — contradiz a convenção "Apenas `config/settings.py` lê env vars" do PROJECT-CONTEXT.md. Padrão difundido no módulo; registrar para o Architect.
- 🔴 **`except (ValidationError, json.JSONDecodeError, AttributeError, Exception)`** em data_extraction_llm.py:70 — `Exception` (catch-all) torna as anteriores redundantes e engole erros de programação, retornando `None` silenciosamente.
- 🟡 **`patient_created` sempre `False`:** `result.patient_created = getattr(result, "_patient_just_created", False)` (user_data_capture.py:124) — o atributo `_patient_just_created` nunca é definido em `CaptureResult`. O campo existe no contrato SSE (`done_payload["patient_created"]`) mas nunca reporta `True`. Possível bug.
- 🟢 **`tokens_used` no streaming é impreciso:** `len(text.split())` conta palavras, não tokens reais — métrica de auditoria diferente da via REST (`provider.usage.total_tokens`).
- 🟢 **`record` (audit) é stub `pass` no MVP** — `GUARDRAIL_BLOCKED`/`MESSAGE_SENT` são chamados mas nada persiste (consistente com achado de `accounts`).
- 🟢 **Captura de `measured_at`/`started_at`/etc. nas regex é mínima:** os campos datetime só vêm via LLM (ISO8601); as regras não extraem datetime. Em `_persist_health_data`, ausentes → `timezone.now()`.
- 🟢 Testes: `tests/ai_engine/` (guardrails, orchestrator, skills, user_data_capture, user_readiness) + `tests/ai_eval/` (`guardrails.yaml` + `run.py` — avaliação de guardrails). Boa cobertura do módulo central.

---

## Módulo: rag

**Caminho:** `django-api/apps/rag/`
**Propósito:** Base de conhecimento com RAG. Ingestão de documentos (PDF/MD/TXT), chunking + embeddings OpenAI, persistência em ChromaDB (local), retrieval por similaridade com score mínimo e endpoints de administração da knowledge base + métricas. Consumido pelo `orchestrator` para contextualizar o chat.

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `upload(request)` | views.py:24 | POST (MultiPart) | 201 `{id, title, status, chunk_count}` |
| `list_documents(request)` | views.py:64 | GET | `list[dict]` (values id/title/status/chunk_count/created_at) |
| `document_status(request, doc_id)` | views.py:73 | GET | `{id, status, chunk_count, error_message}` |
| `metrics(request)` | views.py:90 | GET | `dict` de métricas do dia |
| `delete_document(request, doc_id)` | views.py:119 | DELETE | 204 |
| `ingest(document, file_bytes)` | ingestion.py:38 | `KnowledgeDocument, bytes` | `None` (síncrono; atualiza status) |
| `_extract_text(file_bytes, mime_type)` | ingestion.py:20 | `bytes, str` | `str` (PDF via pypdf; senão utf-8) |
| `_split(text)` | ingestion.py:27 | `str` | `list[str]` (chunks 1000/200) |
| `_get_embeddings()` | ingestion.py:32; retriever.py:10 | — | `OpenAIEmbeddings` (singleton no retriever) |
| `get_collection()` | vector_store.py:14 | — | `Collection` (singleton thread-safe) |
| `search(query, k=5, min_score=0.40)` | retriever.py:19 | `str, int, float` | `list[dict]` `{content, source, chunk_id, document_id, score}` |

**Fluxos principais** (detalhe em `flowcharts/rag.md`):

- **Upload** → valida arquivo presente → `f.size > MAX_BYTES(10MB)` → `FILE_TOO_LARGE`; `content_type ∉ ALLOWED_MIMETYPES` → `INVALID_FILE_TYPE` → cria `KnowledgeDocument(status=PROCESSING)` → **`ingest()` síncrono** → `record("KB_UPLOAD")` → 201.
- **Ingest** → `_extract_text` (PDF: `PdfReader` concatena páginas; MD/TXT: `decode utf-8 errors=replace`) → valida `text.strip()` (vazio → erro) → `_split` (RecursiveCharacterTextSplitter 1000/200) → `OpenAIEmbeddings.embed_documents(chunks)` → `get_collection().add(ids, documents, embeddings, metadatas)` → `status=INDEXED` + `chunk_count`. Exceção → `logger.exception("document_index_failed")` + `status=ERROR` + `error_message=str(e)[:1000]`.
- **Search** → `get_collection()` → `coll.count()==0` → `[]` → `embed_query` → `coll.query(n_results=min(k, count))` → converte distância L² em score de cosseno `max(0, 1 - dist/2)` → filtra `score < min_score` → monta resultado com `source=title`, `chunk_id=chunk_index`, `document_id`.
- **Delete** → busca doc (404 se ausente) → `status==PROCESSING` → 409 `CONFLICT` → `coll.delete(where={"document_id": str(doc.id)})` → `doc.delete()` → `record("KB_DELETE")` → 204.
- **Metrics** → agrega do dia: `users_total`, `conversations_total`, `messages_today`, `tokens_today` (Sum tokens_used), `guardrail_blocks_today` (blocked_by_guardrail), `kb_documents_indexed` (status=INDEXED).

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Tipos aceitos | `{application/pdf, text/markdown, text/plain}`; senão `INVALID_FILE_TYPE` | views.py:16; 32 | 🟢 |
| Tamanho máximo | `MAX_BYTES = 10 MB`; excedeu → `FILE_TOO_LARGE` | views.py:17; 30 | 🟢 |
| Chunking | `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` hardcoded | ingestion.py:28 | 🟢 |
| Score de similaridade | Chroma com `space='l2'`; `score = max(0, 1 - dist/2)` (cosseno em vetores normalizados) | retriever.py:40 | 🟢 |
| Filtro de score | `score < min_score` → descartado. Default da função `0.40`; orquestrador injeta `RAG_MIN_SCORE=0.75` | retriever.py:19, 40; orchestrator.py:127 | 🟢 |
| `n_results` | `min(k, coll.count())` — nunca pede mais que o existente | retriever.py:31 | 🟢 |
| IDs de chunk | `f"{doc.id}-{i}-{uuid4().hex[:8]}"` (único) | ingestion.py:48 | 🟢 |
| Ingestão síncrona | `ingest()` roda dentro do request POST; sem fila/background | views.py:45; ingestion.py:38 | 🟢 |
| Status lifecycle | `PROCESSING → INDEXED | ERROR`; `error_message` truncado a 1000 chars | ingestion.py:59-70 | 🟢 |
| Delete bloqueia PROCESSING | 409 `CONFLICT` se documento ainda em processamento | views.py:124-125 | 🟢 |
| Telemetria off | `ANONYMIZED_TELEMETRY=False` + `chroma_product_telemetry_impl=NoopProductTelemetry` (workaround posthog 7.x) | vector_store.py:23-31 | 🟢 |
| Métricas do dia | `created_at__date=today`; `tokens_today` via `Sum(tokens_used)` | views.py:92-98 | 🟢 |

### 3. Estruturas de dados

- **Entidade:** `KnowledgeDocument` — ver `data-dictionary.md`.
- **ChromaDB:** collection `mediclaw_kb` com `documents` (chunks), `embeddings` (float list) e `metadatas` `{document_id: str, title: str, chunk_index: int}`.

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `COLLECTION_NAME` | `mediclaw_kb` | vector_store.py:11 |
| `CHROMA_PERSIST_DIR` | env obrigatório (sem default) | vector_store.py:21 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` (env) — 1536 dim | ingestion.py:34; retriever.py:14 |
| `ALLOWED_MIMETYPES` | `{application/pdf, text/markdown, text/plain}` | ingestion.py:16 |
| `MAX_BYTES` | `10 * 1024 * 1024` | ingestion.py:17 |
| `chunk_size` / `chunk_overlap` | `1000` / `200` (hardcoded) | ingestion.py:28 |
| `min_score` default (search) | `0.40` | retriever.py:19 |
| `RAG_TOP_K` / `RAG_MIN_SCORE` (orquestrador) | `5` / `0.75` (env) | orchestrator.py:126-127 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| POST | `/api/v1/admin/knowledge/upload/` | `IsAuthenticated` | Upload + ingestão (síncrona) → 201 |
| GET | `/api/v1/admin/knowledge/` | `IsAuthenticated` | Lista documentos |
| GET | `/api/v1/admin/knowledge/<doc_id>/status/` | `IsAuthenticated` | Status + erro de indexação |
| DELETE | `/api/v1/admin/knowledge/<doc_id>/` | `IsAuthenticated` | Deleta doc + chunks do Chroma → 204 |
| GET | `/api/v1/admin/metrics/` | `IsAdminRole` | Métricas do dia (view em `rag/views.py:90`, **roteada em `audit/urls.py:8`**) |

### 6. Dependências

- `langchain_openai.OpenAIEmbeddings`, `langchain_text_splitters.RecursiveCharacterTextSplitter`, `pypdf.PdfReader`, `chromadb`
- `apps.common.exceptions.AppError`, `apps.common.permissions.IsAdminRole`, `apps.common.logging_config`
- `apps.audit.services.log.record` — auditoria (stub no MVP)
- `apps.accounts.models.User`, `apps.conversations.models (Conversation, Message)` — métricas
- **Consumidor:** `apps.ai_engine.orchestrator` (`search`) — injeta chunks como contexto científico no prompt
- **Tabela:** `rag_knowledgedocument` (migration 0001_initial)

### 7. Achados

- 🟢 **`metrics` é roteada em `apps/audit/urls.py`** (→ `/api/v1/admin/metrics/`), não no `urls.py` do próprio `rag` — roteamento cruzado de módulo. Coerente com o namespace admin centralizado.
- 🟢 **Rota sob `/api/v1/admin/` mas só `metrics` exige `IsAdminRole`:** upload/list/status/delete são `IsAuthenticated`. Qualquer usuário autenticado pode adicionar documentos à knowledge base que alimenta as respostas do chat — vetor de conteúdo potencialmente inseguro. 🟡 Registrar para o Architect.
- 🟢 **Ingestão síncrona no request:** `upload` executa extração + embeddings + escrita no Chroma dentro do POST — documento grande (até 10MB) pode travar o request por segundos. Sem fila/background, sem `celery`. 🟡 Oportunidade de otimização pós-MVP.
- 🟢 **Divergência de `min_score`:** `search()` usa default `0.40`, mas o orquestrador injeta `RAG_MIN_SCORE=0.75` e o PROJECT-CONTEXT.md documenta `score ≥ 0.75`. O default da função só vale se chamada sem o env — comportamento inconsistente documentado.
- 🟢 **`record` inconsistente:** rag/views.py chama `record(..., user=request.user, ...)` (kwarg correto da assinatura), mas `orchestrator.py` chama `record(..., user_id=user_id, ...)` que cai em `**kwargs`. Stub no MVP, mas divergência de contrato.
- 🟢 **Sem varredura automática de `knowledge_base/`:** o diretório de documentos fonte existe (surface.json), mas a ingestão é manual via upload HTTP. Não há command de importação em lote.
- 🟢 **Sem migrations para `pgvector`:** Chroma local conforme planejado; migração futura fica para pós-MVP.
- 🟢 **Embeddings só OpenAI:** coerente com o achado de `ai_engine` (provider Anthropic documentado, código usa OpenAI/Gemini para chat e OpenAI para embeddings).
- 🟢 Testes: `tests/rag/` — `test_ingestion.py` (txt/pdf/erro), `test_retriever.py` (coleção vazia, score alto, filtro `min_score`, chaves do resultado), `test_views.py` (upload/list/status/delete). Embeddings mockados com hash MD5 determinístico; Chroma em tmp_path.

---

## Módulo: audit

**Caminho:** `django-api/apps/audit/`
**Propósito:** Camada de auditoria e métricas internas. No MVP é **um stub**: `record()` é um `pass` que não persiste nada (previsto para expandir no Epic 3). O `urls.py` funciona como hub de rotas admin, roteando views de outros apps (criação admin de usuário e métricas).

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `record(event, *, user=None, **kwargs)` | services/log.py:1 | `str, user, **kwargs` | `None` — **stub `pass`** |
| `admin_create_user` (roteada) | audit/urls.py:7 | view de `apps/accounts.views` | — |
| `metrics` (roteada) | audit/urls.py:8 | view de `apps/rag.views` | — |

**Fluxo principal:** nenhum fluxo próprio — o módulo apenas expõe `record()` (no-op) e agrupa as rotas admin `/api/v1/admin/users/` e `/api/v1/admin/metrics/`.

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Auditoria no-op | `record` é `pass` — chamadas não produzem efeito no MVP | services/log.py:3 | 🟢 |
| Contrato do evento | `record(event: str, *, user=None, **kwargs)` — metadados via `**kwargs` | services/log.py:1 | 🟢 |
| Namespace admin | `audit/urls.py` monta `users/` e `metrics/` sob `/api/v1/admin/` | urls.py:6-9 | 🟢 |
| `record` com `user=` | accounts e rag usam o kwarg correto `user=...` | accounts/views.py:26,46,62; rag/views.py:46,130 | 🟢 |
| `record` com `user_id=` | orchestrator usa `user_id=...` (cai em `**kwargs`, divergente do contrato) | ai_engine/orchestrator.py:200,226,245 | 🟢 |

### 3. Estruturas de dados

- **Entidades ORM:** **nenhuma.** Não existe modelo `ActivityLog` apesar do PROJECT-CONTEXT.md documentar `audit/ # ActivityLog, métricas internas`. 🔴 LACUNA — requisito de auditoria pendente.

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| Rotas | `/api/v1/admin/users/` (admin_create_user), `/api/v1/admin/metrics/` (metrics) | urls.py:7-8; config/urls.py:36 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| POST | `/api/v1/admin/users/` | `IsAdminRole` | Cria usuário (view de `accounts`) |
| GET | `/api/v1/admin/metrics/` | `IsAdminRole` | Métricas do dia (view de `rag`) |

### 6. Dependências

- **Inbound (chamadores de `record`):** `apps.accounts.views` (`USER_REGISTERED`, `LOGIN`, `ADMIN_CREATED_USER`), `apps.rag.views` (`KB_UPLOAD`, `KB_DELETE`), `apps.ai_engine.orchestrator` (`GUARDRAIL_BLOCKED` ×2, `MESSAGE_SENT`)
- **Outbound (rotas):** `apps.accounts.views.admin_create_user`, `apps.rag.views.metrics`

### 7. Achados

- 🔴 **`ActivityLog` não existe:** o módulo documentado como "ActivityLog, métricas internas" não tem models/views próprios — apenas `record()` stub. Todos os eventos (`USER_REGISTERED`, `LOGIN`, `ADMIN_CREATED_USER`, `KB_UPLOAD`, `KB_DELETE`, `GUARDRAIL_BLOCKED`, `MESSAGE_SENT`) são descartados silenciosamente. Epic 3 pendente.
- 🟢 **Roteamento cruzado:** `audit/urls.py` é hub de views de outros apps (accounts, rag) — padrão de namespace admin centralizado, mas a responsabilidade "métricas" fica fisicamente em `rag/views.py` (incoerência de localização).
- 🟢 **`user=` vs `user_id=`:** dois contratos de chamada convivem. Como `record` é `pass`, não quebra hoje; na implementação do Epic 3 a assinatura precisa ser padronizada.
- 🟢 Sem testes dedicados (nada a testar em um `pass`).

---

## Módulo: common

**Caminho:** `django-api/apps/common/`
**Propósito:** Infraestrutura transversal do projeto — envelope de resposta (renderer + exception handler), middlewares (request ID, contexto de usuário), permissões customizadas, paginação padrão, configuração de logging structlog e health check. Wire no `settings.py` e no `apps.py` (configure_structlog no startup).

### 1. Fluxo de controle

| Função | Arquivo:linha | Parâmetros | Retorno |
|---|---|---|---|
| `AppError(code, message, status_code=400, details=None)` | exceptions.py:5 | `str, str, int, dict\|None` | `APIException` com `detail={code, message, details}` |
| `GuardrailBlockedError(reason)` | exceptions.py:21 | `str` | `AppError("GUARDRAIL_BLOCKED", reason, 200)` |
| `LLMProviderError(message)` | exceptions.py:26 | `str` | `AppError("LLM_PROVIDER_ERROR", message, 502)` |
| `envelope_exception_handler(exc, context)` | exceptions.py:31 | `exc, context` | `Response` envelopado ou `None` |
| `EnvelopeJSONRenderer.render(data, ...)` | renderers.py:4 | `data, media_type, context` | `str` JSON com envelope |
| `RequestIDMiddleware.__call__(request)` | middleware.py:15 | `request` | `response` (injeta `X-Request-ID`, loga latency) |
| `UserContextMiddleware.__call__(request)` | middleware.py:51 | `request` | `response` (bind `user_id` no contextvar) |
| `IsAdminRole.has_permission(request, view)` | permissions.py:4 | `request, view` | `bool` (role == "ADMIN") |
| `IsOwner.has_object_permission(request, view, obj)` | permissions.py:13 | `request, view, obj` | `bool` (owner = doctor\|user\|uploaded_by) |
| `health(request)` | views.py:19 | `request` | `{status, db, vector_store, version}` — 200/503 |
| `configure_structlog(*, debug)` | logging_config.py:24 | `bool` | `None` |
| `get_logging_config(*, debug)` | logging_config.py:36 | `bool` | `dict` (LOGGING do settings) |
| `get_logger(name)` | logging_config.py:82 | `str` | `BoundLogger` structlog |
| `DefaultPagination` | pagination.py:4 | — | `PageNumberPagination` (20/100) |

**Fluxos principais:**

- **Envelope de resposta** → `EnvelopeJSONRenderer` envolve todo `data` em `{data, error: null, meta: {}}` a menos que já contenha as chaves `data`/`error` (evita re-envelope). Erros DRF passam por `envelope_exception_handler`: se `payload` tem `code`, usa o payload; senão `{code: UNHANDLED, message: str(payload)}`. Ambos configurados globalmente no settings.
- **Request ID** → `RequestIDMiddleware` lê `X-Request-ID` (ou gera `uuid4`), bind no contextvar, loga `request_completed`/`request_failed` com `method`, `path`, `status_code`, `latency_ms` (perf_counter) — sem PII; injeta `X-Request-ID` no response.
- **User context** → `UserContextMiddleware` bind `user_id` no contextvar se autenticado (structlog merge_contextvars adiciona ao log).
- **Health** → `GET /health/` (AllowAny): `SELECT 1` no Postgres + `get_collection().count()` no Chroma → `status: ok|degraded` (200/503), `version: "0.1.0"` hardcoded.
- **Logging** → `configure_structlog` roda no `ready()` do `CommonConfig`; `LOGGING` do settings usa `get_logging_config(debug=settings.DEBUG)` — ConsoleRenderer (dev) vs JSONRenderer (prod); loggers ruidosos (`urllib3`, `chromadb`, `httpx`, `httpcore`) em WARNING.

### 2. Algoritmos e regras de negócio

| Regra | Detalhe | Local | Confiança |
|---|---|---|---|
| Envelope duplo evitado | Renderer só envolve se `data` não tiver chaves `data`/`error` | renderers.py:6 | 🟢 |
| Erro com `code` | `envelope_exception_handler` usa payload DRF se tiver `code`; senão `UNHANDLED` | exceptions.py:36-43 | 🟢 |
| Erros não-DRF | Retorna `None` → cai no handler padrão (500) do Django | exceptions.py:33-34 | 🟢 |
| `LLMProviderError` | 502 no envelope — propagada pelos providers OpenAI/Gemini | exceptions.py:26-28; providers | 🟢 |
| `GuardrailBlockedError` | 200 — **não usada**: guardrail retorna `GenerateResult(blocked=True)` | exceptions.py:21-23; orchestrator | 🟢 |
| Request ID | Header `X-Request-ID` ou `uuid4`; propagado no response | middleware.py:17, 32 | 🟢 |
| Health degradado | DB ou vector store falhou → `status: degraded` + 503 | views.py:28-37 | 🟢 |
| `IsOwner` | owner = `doctor` \| `user` \| `uploaded_by` (getattr chain) | permissions.py:15-18 | 🟢 |
| Nível de log | `LOG_LEVEL` env (padrão `INFO`); ruído de libs em `WARNING` | logging_config.py:37, 74-77 | 🟢 |

### 3. Estruturas de dados

- **Entidades ORM:** nenhuma. Módulo de infraestrutura pura (classes, funções, middlewares).

### 4. Metadados e configuração

| Item | Valor | Local |
|---|---|---|
| `REST_FRAMEWORK.DEFAULT_RENDERER_CLASSES` | `apps.common.renderers.EnvelopeJSONRenderer` | settings.py:120 |
| `REST_FRAMEWORK.DEFAULT_PAGINATION_CLASS` | `apps.common.pagination.DefaultPagination` (20/`page_size`/100) | settings.py:121 |
| `REST_FRAMEWORK.EXCEPTION_HANDLER` | `apps.common.exceptions.envelope_exception_handler` | settings.py:128 |
| `MIDDLEWARE` | `RequestIDMiddleware`, `UserContextMiddleware` | settings.py:63, 70 |
| `INSTALLED_APPS` | `apps.common.apps.CommonConfig` (ready → configure_structlog) | settings.py:52; apps.py:9-13 |
| `LOG_LEVEL` | env `INFO` (padrão) | logging_config.py:37 |
| Health version | `"0.1.0"` (hardcoded) | views.py:35 |
| `DefaultPagination` | `page_size=20`, `page_size_query_param="page_size"`, `max_page_size=100` | pagination.py:5-7 |
| Loggers silenciados | `urllib3`, `chromadb`, `httpx`, `httpcore` → `WARNING` | logging_config.py:74-77 |

### 5. Endpoints

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/health/` | `AllowAny` | Health check (DB + Chroma) — fora do `/api/v1/` |

> Note: `/api/v1/health/` aponta para `health_logs.urls` (resumo agregado), não para este health check.

### 6. Dependências

- **Inbound:** todos os apps importam `apps.common` (exceptions, permissions, logging_config, renderers via settings).
- **Outbound:** `apps.rag.vector_store.get_collection` (health), `django.db.connection` (health).
- Bibliotecas: `structlog`, `rest_framework`.
- **Consumido globalmente:** settings.py (renderer, pagination, exception handler, middleware, logging).

### 7. Achados

- 🟢 **`IsOwner` é código morto** — definida em permissions.py:13 mas nenhum view a usa (as views filtram `doctor=request.user` nas querysets). Sem remover; registrar para o Architect (pode substituir o padrão de queryset).
- 🟢 **`GuardrailBlockedError` é código morto** — o orchestrator não a lança; guardrail bloqueia retornando `GenerateResult(blocked=True)` (REST) ou evento `done blocked` (SSE). A exceção existe mas nunca é usada.
- 🟢 **Health com versão hardcoded `"0.1.0"`** — sem fonte única de versão (pyproject/settings); tende a desatualizar.
- 🟢 **Health `AllowAny` fora do `/api/v1/`** — exposto sem auth (intencional para probe/load balancer). O Dockerfile.prod healthcheck usa este endpoint com headers customizados.
- 🟢 **`configure_structlog` no `ready()`** — roda em cada worker/runserver; idempotente. Padrão correto de bootstrap de logging.
- 🟢 **Renderer re-envelope evitado por checagem de chaves** — sem risco de envelope duplo entre handler e renderer.
- 🟡 `envelope_exception_handler` com payload não-dict (ex.: string) cai em `UNHANDLED` — sem detalhe real do erro; aceitável no MVP, mas perde diagnóstico.
- 🟢 Sem testes dedicados para `common` (infra configurada via settings; coberta indiretamente por integração).

---

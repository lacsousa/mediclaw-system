# Health Logs, Design Técnico

> Contrato operacional de **COMO** a unit `health_logs` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

### Endpoints HTTP

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/health/weight/` | `patient_id` (obrigatório), `from?`, `to?` | lista paginada de `WeightLog` | 200, 401, 404 | `IsAuthenticated` |
| POST | `/api/v1/health/weight/` | `{patient_id, value_kg, measured_at?}` | `WeightLog` | 201, 400, 401, 404 | `IsAuthenticated` |
| DELETE | `/api/v1/health/weight/<id>/` | — | `204 No Content` | 204, 401, 404 | `IsAuthenticated` |
| GET/POST/DELETE | `/api/v1/health/sleep/` | análogo (`duration_hours`, `quality_score`, `started_at`) | `SleepLog` | 200, 201, 204, 400, 401, 404 | `IsAuthenticated` |
| GET/POST/DELETE | `/api/v1/health/activity/` | análogo (`type`, `duration_min`, `performed_at`) | `ActivityLog` | 200, 201, 204, 400, 401, 404 | `IsAuthenticated` |
| GET/POST/DELETE | `/api/v1/health/nutrition/` | análogo (`note`, `logged_at`) | `NutritionNote` | 200, 201, 204, 400, 401, 404 | `IsAuthenticated` |
| GET | `/api/v1/health/summary/` | `patient_id` (obrigatório), `window` ∈ {7, 30} | resumo agregado (dict) | 200, 400, 401, 404 | `IsAuthenticated` |

PUT/PATCH retornam `405` (ViewSets com `http_method_names = ["get", "post", "delete"]`). 🟢
`patient_id` chega via query param na listagem e no body no create; nunca em rota de sub-recurso. 🟢

### Funções / classes

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `_PatientQuerysetMixin.get_queryset` | `(self) -> QuerySet` | QS filtrado | `patient_id` obrigatório; senão `.none()`; aplica `from`/`to` no `timestamp_field` |
| `_PatientQuerysetMixin.perform_create` | `(self, serializer) -> None` | — | Exige `patient_id`, valida ownership, salva com `patient_id` |
| `_get_patient_or_404` | `(request, patient_id: int) -> Patient` | `Patient` | `Patient.objects.get(pk, doctor=request.user)`; senão `AppError NOT_FOUND` |
| `summarize` | `(patient_id: int, window_days: int = 7) -> dict` | resumo | Agrega sono, peso, atividade e notas |
| `persist_weight_log` / `persist_sleep_log` / `persist_activity_log` / `persist_nutrition_note` | `(patient_id: int, data: dict[str, Any]) -> dict[str, Any]` | metadados do log | Captura via chat; validações próprias |

## Fluxo Principal

### 1. Listagem de logs (`GET /api/v1/health/<tipo>/`)

1. `_PatientQuerysetMixin.get_queryset`: lê `patient_id` do query param; se ausente → `.none()` (lista vazia, sem erro). (`apps/health_logs/views.py:30-33`) 🟢
2. `_get_patient_or_404` valida ownership do paciente. (`apps/health_logs/views.py:34`) 🟢
3. Filtra por `patient_id` e, se presentes, `{ts_field}__gte=from` e `{ts_field}__lte=to`. (`apps/health_logs/views.py:35-43`) 🟢
4. Paginação via `DefaultPagination` global (`PageNumberPagination`, `page_size=20`, `page_size` query param, máx 100). (`config/settings.py:121-122`; `apps/common/pagination.py`) 🟢
5. Serializa com o serializer do tipo e devolve no envelope `{data, error, meta}` via `EnvelopeJSONRenderer`. (`apps/common/renderers.py`) 🟢

### 2. Criação de log (`POST /api/v1/health/<tipo>/`)

1. `perform_create` exige `patient_id` no body; ausente → `ValidationError {"patient_id": "Obrigatório."}`. (`apps/health_logs/views.py:45-50`) 🟢
2. `_get_patient_or_404` valida ownership. (`apps/health_logs/views.py:51`) 🟢
3. Serializer valida o payload (faixas por tipo) e `serializer.save(patient_id=int(patient_id))`. (`apps/health_logs/views.py:52`) 🟢
4. Retorna 201 com o objeto serializado. 🟢

### 3. Deleção de log (`DELETE /api/v1/health/<tipo>/<id>/`)

- ViewSet `destroy` padrão; objeto já filtrado pelo mixin (list queryset) → fora do escopo cai em 404. 🟢

### 4. Resumo agregado (`GET /api/v1/health/summary/`)

1. Exige `patient_id` (400 se ausente) e valida ownership (404). (`apps/health_logs/views.py:89-92`) 🟢
2. `window = int(query_params.get("window", "7"))`; se não estiver em (7, 30) → `window = 7`. (`apps/health_logs/views.py:93-95`) 🟢
3. `summarize(patient_id, window)`:
   - `since = now - timedelta(days=window)` (`services/aggregate.py:10`)
   - Média de `duration_hours` e `quality_score` do sono na janela (`Avg`). (`aggregate.py:12-14`)
   - `latest_weight` (mais recente, sem janela) e `first_weight` (primeiro na janela); `weight_trend = latest - first` (ou `None`). (`aggregate.py:16-32`)
   - `total_activity = Sum(duration_min)` na janela (`or 0`). (`aggregate.py:34-39`)
   - `last_nutrition_notes` = 3 notas mais recentes (`order_by("-logged_at")[:3]`). (`aggregate.py:41-45`)
4. Retorna dict: `window_days`, `avg_sleep_hours`, `avg_sleep_quality`, `latest_weight_kg`, `weight_trend_kg`, `total_activity_min`, `last_nutrition_notes`. 🟢

### 5. Captura via chat (`persist_*`)

1. `persist_weight_log`: valida `20 ≤ value_kg ≤ 400`; `measured_at` default `timezone.now()`; rejeita data futura; cria e retorna metadados. (`services/persist.py:21-36`) 🟢
2. `persist_sleep_log`: valida `0 < duration_hours ≤ 24`; `quality_score` default `5` (constante `DEFAULT_SLEEP_QUALITY`), faixa 1–10; rejeita data futura. (`services/persist.py:39-59`) 🟢
3. `persist_activity_log`: `duration_min ≥ 1`; `type` obrigatório, truncado a 40 chars; rejeita data futura. (`services/persist.py:62-84`) 🟢
4. `persist_nutrition_note`: `note` com `10 ≤ len ≤ 1000` (constante `MIN_NUTRITION_NOTE_LEN`); rejeita data futura. (`services/persist.py:87-100`) 🟢

## Fluxos Alternativos

- **[Sem `patient_id` na listagem]:** queryset `.none()` → resposta 200 com lista vazia (não é erro). 🟢
- **[`patient_id` fora do escopo]:** `_get_patient_or_404` → 404 `NOT_FOUND` em qualquer operação. 🟢
- **[Peso/duração/qualidade fora da faixa]:** `ValidationError` do serializer (400 no envelope). 🟢
- **[Data futura]:** `validate_*` rejeita `measured_at`/`started_at`/`performed_at`/`logged_at` > `timezone.now()`. 🟢
- **[Window inválida no summary]:** fallback silencioso para 7 dias (sem erro). 🟢
- **[Log inexistente na deleção]:** 404 do ViewSet padrão. 🟡

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.patients.models.Patient` | Vínculo e ownership | FK em todos os logs; `_get_patient_or_404` (`views.py:19-24`) |
| `apps.common.exceptions.AppError` | `NOT_FOUND` / `VALIDATION_ERROR` com envelope | `views.py:23-24,91` |
| `apps.common.pagination.DefaultPagination` | Paginação default dos ViewSets | Global via settings |
| `apps.common.renderers.EnvelopeJSONRenderer` | Envelope `{data, error, meta}` | Global via settings |
| `rest_framework.viewsets.ModelViewSet` | CRUD imutável | 4 ViewSets com `http_method_names` |
| `django.db.models` | Agregações | `Avg`, `Sum` em `aggregate.py` |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| 4 modelos separados por tipo (não um único `HealthLog` com tipo) | `apps/health_logs/models.py:4-59` | 🟢 |
| Logs imutáveis: sem PUT/PATCH, apenas create/list/delete | `apps/health_logs/views.py:60,68,76,84` | 🟢 |
| `patient_id` via query param (listagem) e body (create) — não sub-recurso `/patient/<id>/logs` | `apps/health_logs/views.py:31,46` | 🟢 |
| Ownership validado a cada acesso (queryset + `_get_patient_or_404`) | `apps/health_logs/views.py:19-24,34,51` | 🟢 |
| Filtro temporal dinâmico via `timestamp_field` por tipo | `apps/health_logs/views.py:36-42,59,67,75,83` | 🟢 |
| Validação de faixa duplicada entre serializer (API) e service (chat) | `apps/health_logs/serializers.py`; `services/persist.py` | 🟢 |
| Resumo com duas querys de peso (latest sem janela + first na janela) para tendência | `apps/health_logs/services/aggregate.py:16-32` | 🟢 |
| `summarize` usa 4 queries separadas (sem JOIN) | `apps/health_logs/services/aggregate.py:12-45` | 🟡 |
| Segurança herdada do default global (`IsAuthenticated` + throttling) | `config/settings.py:115-127` | 🟢 |

## Estado Interno

| Modelo | Campos | Ordenação / índice |
|--------|--------|--------------------|
| `WeightLog` | `patient` FK, `value_kg` Decimal(5,2), `measured_at` | `-measured_at`; índice `(patient, -measured_at)` |
| `SleepLog` | `patient` FK, `duration_hours` Decimal(4,2), `quality_score` PositiveSmallInt, `started_at` | `-started_at`; índice `(patient, -started_at)` |
| `ActivityLog` | `patient` FK, `type` Char(40), `duration_min` PositiveSmallInt, `performed_at` | `-performed_at`; índice `(patient, -performed_at)` |
| `NutritionNote` | `patient` FK, `note` Text, `logged_at` | `-logged_at`; índice `(patient, -logged_at)` |

Todos `on_delete=CASCADE` para o paciente (remoção em cascata — LGPD). 🟢

## Observabilidade

- Sem logs explícitos nos ViewSets e no `summarize`. 🟡
- Services de persistência não logam criação (diferente de `patients/services/patient.py` que loga `patient_created`). 🟡
- Throttling global ativo fornece limite implícito, mas sem métricas de taxa de erro. 🟢 (throttle) / 🟡 (métricas)

## Riscos e Lacunas

- 🔴 Inconsistência de validação entre serializer e service de captura: `SleepLogSerializer` não valida `duration_hours` (0–24) nem rejeita data futura em `started_at`, mas `persist_sleep_log` valida — comportamentos divergentes entre API e chat.
- 🔴 `NutritionNoteSerializer` (API) não aplica o mínimo de 10 chars que o `persist_nutrition_note` exige — regra de mínimo só na captura via chat.
- 🟡 `health_summary` não declara `permission_classes` explicitamente — a proteção depende do default global `IsAuthenticated`; se o default mudar, o endpoint fica aberto.
- 🟡 `summarize` roda 4+ queries sem transação — em carga alta, dados podem divergir levemente entre medições.
- 🟡 `window` fora de (7, 30) cai para 7 silenciosamente — sem erro, pode confundir o cliente.
- 🟡 Sem validação de intervalo `from ≤ to` nos filtros de listagem (comportamento com `from > to` não definido).

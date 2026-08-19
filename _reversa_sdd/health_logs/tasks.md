# Health Logs, Tarefas de Implementação

> Sequência executável para reimplementar a unit `health_logs` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Unit `patients` implementada (FK `patient` aponta para `patients.Patient`)
- [ ] Infra de envelope e erros da unit `common` (renderer `EnvelopeJSONRenderer`, `AppError` com code `NOT_FOUND`/`VALIDATION_ERROR`, `DefaultPagination`)
- [ ] `config/settings.py` com default global `IsAuthenticated`, autenticação JWT e throttling configurados
- [ ] Schema PostgreSQL criado e migrations aplicadas

## Tarefas

- [ ] **T-01**, Quatro modelos de log com FK `CASCADE` e índices compostos
  - Origem no legado: `apps/health_logs/models.py:4-59`
  - Critério de pronto: migration cria `WeightLog` (`value_kg` Decimal(5,2), `measured_at`), `SleepLog` (`duration_hours` Decimal(4,2), `quality_score` PositiveSmallInt, `started_at`), `ActivityLog` (`type` Char(40), `duration_min` PositiveSmallInt, `performed_at`) e `NutritionNote` (`note` Text, `logged_at`); todos com FK `patient` `on_delete=CASCADE`, `related_name` singular plural (`weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes`), índice `(patient, -timestamp)` e ordering `-timestamp` por tipo
  - Confiança: 🟢

- [ ] **T-02**, Serializer `WeightLogSerializer` com validações de faixa e data futura
  - Origem no legado: `apps/health_logs/serializers.py:7-23`
  - Critério de pronto: fields `[id, value_kg, measured_at]`, `id` read-only; `validate_value_kg` rejeita fora de 20–400 kg; `validate_measured_at` rejeita `> timezone.now()`
  - Confiança: 🟢

- [ ] **T-03**, Serializer `SleepLogSerializer` com `quality_score` 1–10
  - Origem no legado: `apps/health_logs/serializers.py:26-35`
  - Critério de pronto: fields `[id, duration_hours, quality_score, started_at]`; `validate_quality_score` rejeita fora de 1–10
  - Confiança: 🟢

- [ ] **T-04**, Serializer `ActivityLogSerializer` com `duration_min ≥ 1`
  - Origem no legado: `apps/health_logs/serializers.py:38-46`
  - Critério de pronto: fields `[id, type, duration_min, performed_at]`; `validate_duration_min` rejeita `< 1`
  - Confiança: 🟢

- [ ] **T-05**, Serializer `NutritionNoteSerializer` com limite de 1000 chars
  - Origem no legado: `apps/health_logs/serializers.py:50-59`
  - Critério de pronto: fields `[id, note, logged_at]`; `validate_note` rejeita `len > 1000`
  - Confiança: 🟢

- [ ] **T-06**, Helper `_get_patient_or_404` (ownership do médico)
  - Origem no legado: `apps/health_logs/views.py:19-24`
  - Critério de pronto: `Patient.objects.get(pk=patient_id, doctor=request.user)`; `DoesNotExist` → `AppError("NOT_FOUND", ..., 404)`
  - Confiança: 🟢

- [ ] **T-07**, Mixin `_PatientQuerysetMixin` (queryset filtrado + perform_create)
  - Origem no legado: `apps/health_logs/views.py:27-52`
  - Critério de pronto: `get_queryset` sem `patient_id` → `.none()`; com `patient_id` valida ownership e filtra, aplicando `from`/`to` no `timestamp_field` (`__gte`/`__lte`); `perform_create` exige `patient_id` no body (senão `ValidationError {"patient_id": "Obrigatório."}`), valida ownership e salva com `patient_id=int(patient_id)`
  - Confiança: 🟢

- [ ] **T-08**, Quatro ViewSets imutáveis (get/post/delete)
  - Origem no legado: `apps/health_logs/views.py:55-84`
  - Critério de pronto: `WeightLogViewSet`, `SleepLogViewSet`, `ActivityLogViewSet`, `NutritionNoteViewSet` herdam mixin + `ModelViewSet`; cada um com `permission_classes=[IsAuthenticated]`, `timestamp_field` próprio (`measured_at`, `started_at`, `performed_at`, `logged_at`) e `http_method_names=["get", "post", "delete"]` (PUT/PATCH → 405)
  - Confiança: 🟢

- [ ] **T-09**, Endpoint `health_summary` com janela 7/30
  - Origem no legado: `apps/health_logs/views.py:87-96`
  - Critério de pronto: GET exige `patient_id` (400 `VALIDATION_ERROR` se ausente) e valida ownership (404); `window = int(query_params.get("window", "7"))`; se não estiver em (7, 30) → 7; responde com dict de `summarize`
  - Confiança: 🟢

- [ ] **T-10**, Service `summarize` (agregação de sono, peso, atividade e notas)
  - Origem no legado: `apps/health_logs/services/aggregate.py:9-55`
  - Critério de pronto: `since = now - timedelta(days=window_days)`; média de `duration_hours` e `quality_score` do sono na janela (`Avg`, `None` se sem dados); `latest_weight_kg` (mais recente, sem janela) e `first_weight` na janela; `weight_trend_kg = latest - first` (ou `None`); `total_activity_min = Sum(duration_min) or 0` na janela; `last_nutrition_notes` = 3 notas mais recentes; retorna dict com as 7 chaves documentadas em `design.md`
  - Confiança: 🟢

- [ ] **T-11**, Service `persist_weight_log` (captura via chat)
  - Origem no legado: `apps/health_logs/services/persist.py:15-36`
  - Critério de pronto: valida `20 ≤ value_kg ≤ 400`; `measured_at` default `timezone.now()`; rejeita data futura (`_validate_not_future`); cria `WeightLog` e retorna `{id, value_kg (float), measured_at (isoformat)}`
  - Confiança: 🟢

- [ ] **T-12**, Service `persist_sleep_log` (captura via chat)
  - Origem no legado: `apps/health_logs/services/persist.py:39-59`
  - Critério de pronto: valida `0 < duration_hours ≤ 24`; `quality_score` default `DEFAULT_SLEEP_QUALITY=5`, faixa 1–10; `started_at` default `now`, rejeita futuro; cria e retorna metadados
  - Confiança: 🟢

- [ ] **T-13**, Service `persist_activity_log` (captura via chat)
  - Origem no legado: `apps/health_logs/services/persist.py:62-84`
  - Critério de pronto: `duration_min ≥ 1`; `type` obrigatório (strip, vazio → erro), truncado a 40 chars; `performed_at` default `now`, rejeita futuro; cria e retorna metadados
  - Confiança: 🟢

- [ ] **T-14**, Service `persist_nutrition_note` (captura via chat)
  - Origem no legado: `apps/health_logs/services/persist.py:87-100`
  - Critério de pronto: `note` com `MIN_NUTRITION_NOTE_LEN=10 ≤ len ≤ 1000`; `logged_at` default `now`, rejeita futuro; cria e retorna `{id, note, logged_at}`
  - Confiança: 🟢

- [ ] **T-15**, Rotas da unit
  - Origem no legado: `apps/health_logs/urls.py:12-21`
  - Critério de pronto: `DefaultRouter` registra `weight`, `sleep`, `activity`, `nutrition` (basenames) e `path("summary/", health_summary)`; montado em `api/v1/health/`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Listagem: 2 logs de peso de um paciente → 200 paginado, ordenado por `-measured_at`, envelope `{data, error, meta}`
- [ ] **TT-02**, Listagem sem `patient_id` → 200 com lista vazia (não é erro)
- [ ] **TT-03**, Listagem com `from`/`to` → filtra por `measured_at`/`started_at`/`performed_at`/`logged_at` conforme o tipo
- [ ] **TT-04**, Ownership: `patient_id` de outro médico → 404 `NOT_FOUND` na listagem e na criação
- [ ] **TT-05**, Criação `WeightLog`: `value_kg=500` → 400; `measured_at` no futuro → 400; payload válido → 201
- [ ] **TT-06**, `SleepLog`: `quality_score=11` → 400; `ActivityLog`: `duration_min=0` → 400; `NutritionNote`: `note` com 1001 chars → 400
- [ ] **TT-07**, `perform_create` sem `patient_id` no body → 400 com `{"patient_id": "Obrigatório."}`
- [ ] **TT-08**, Imutabilidade: PUT/PATCH em qualquer ViewSet → 405 Method Not Allowed
- [ ] **TT-09**, DELETE → 204; log inexistente → 404
- [ ] **TT-10**, Summary: `window=30` com dados → campos corretos; `window=90` → `window_days=7` (fallback); sem `patient_id` → 400
- [ ] **TT-11**, `summarize` sem dados → `avg_*`/`latest_weight_kg`/`weight_trend_kg` = `None`, `total_activity_min=0`, `last_nutrition_notes=[]`
- [ ] **TT-12**, `persist_sleep_log` com `duration_hours=0` → erro; `quality_score` ausente → default 5
- [ ] **TT-13**, `persist_activity_log` com `type` de 50 chars → truncado a 40; `type` vazio → erro
- [ ] **TT-14**, `persist_nutrition_note` com `note` < 10 chars → erro; 10–1000 → cria
- [ ] **TT-15**, Cascade: deletar paciente remove todos os 4 tipos de log (LGPD)

## Tarefas de Migração de Dados (se aplicável)

- n/a — reimplementação do schema a partir do zero. 🟡

## Ordem Sugerida

1. T-01 (modelos) + T-15 (rotas) primeiro: base da unit.
2. T-02 → T-05 (serializers) e T-06 → T-09 (views) — dependem dos modelos.
3. T-10 (summary) — depende dos 4 modelos.
4. T-11 → T-14 (services de captura) — dependem dos modelos; usados pelo `ai_engine` no onboarding automático (ADR-004).
5. Testes TT-01 a TT-10 (HTTP) após views; TT-11 a TT-14 (services) e TT-15 (cascade) após modelos prontos.

## Lacunas Pendentes (🔴)

- [ ] Inconsistência de validação entre serializer (API) e service (chat): `SleepLogSerializer` não valida `duration_hours` (0–24) nem data futura em `started_at`; `persist_sleep_log` valida — decidir se a API passa a validar igual.
- [ ] `NutritionNoteSerializer` (API) não aplica o mínimo de 10 chars que o `persist_nutrition_note` exige — regra de mínimo só na captura via chat.
- [ ] `health_summary` não declara `permission_classes` explicitamente — proteção depende do default global `IsAuthenticated`; se o default mudar, o endpoint fica aberto.
- [ ] `window` fora de (7, 30) cai para 7 silenciosamente — sem erro, pode confundir o cliente.
- [ ] Sem validação de intervalo `from ≤ to` nos filtros de listagem (comportamento com `from > to` não definido).

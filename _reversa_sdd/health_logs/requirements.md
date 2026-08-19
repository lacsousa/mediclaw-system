# Health Logs — Requisitos

> Contrato operacional da unit `health_logs` (logs biométricos: peso, sono, atividade, refeições).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Módulo de registro de dados biométricos por paciente: quatro entidades — `WeightLog` (peso), `SleepLog` (sono), `ActivityLog` (atividade) e `NutritionNote` (refeições) — expostas como CRUD restrito (listar/criar/deletar, sem edição) via ViewSets, sempre escopadas ao `patient_id` do médico autenticado, com filtros de janela temporal. Inclui endpoint de resumo agregado (`/summary/`) e services de persistência para captura via chat (`persist_*`).

## Responsabilidades

- Persistir logs de peso, sono, atividade e refeições vinculados a um paciente
- Listar/criar/deletar logs (imutáveis — sem PUT/PATCH) por paciente, com filtro temporal `from`/`to`
- Garantir ownership: `patient_id` deve pertencer ao médico autenticado (404 caso contrário)
- Validar faixas plausíveis (peso 20–400 kg, qualidade de sono 1–10, duração de atividade ≥ 1 min, nota ≤ 1000 chars)
- Agregar resumo biométrico em janela de 7 ou 30 dias (`health_summary` / `summarize`)
- Suportar a captura automática via chat (`persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note`)

## Regras de Negócio

- **RN-01** — Todo log pertence a um paciente via FK `on_delete=CASCADE` (remove em cascata com o paciente). 🟢
- **RN-02** — Acesso escopado: `patient_id` deve ser do médico autenticado; caso contrário → 404 `NOT_FOUND`. 🟢
- **RN-03** — `patient_id` é obrigatório na listagem e na criação (lista vazia ou erro 400 se ausente). 🟢
- **RN-04** — Logs são imutáveis: `http_method_names = get/post/delete` (sem PUT/PATCH). 🟢
- **RN-05** — Filtro temporal `from`/`to` aplicado ao campo timestamp de cada tipo (`measured_at`, `started_at`, `performed_at`, `logged_at`). 🟢
- **RN-06** — Peso válido entre 20 e 400 kg; `measured_at` não pode ser no futuro. **No HTTP, apenas o peso valida timestamp futuro** (validador do `WeightLogSerializer`); sono/atividade/nutrição validam data futura somente na via chat. 🟢/🟡 [Revisão Codex]
- **RN-07** — Qualidade de sono entre 1 e 10; duração de atividade ≥ 1 min; nota ≤ 1000 chars. 🟢
- **RN-08** — Resumo aceita `window` ∈ {7, 30}; valores fora caem em 7. 🟢
- **RN-09** — Na captura via chat: duração de sono em (0, 24]; nota com mínimo de 10 chars; tipo de atividade obrigatório e truncado a 40 chars. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Listar logs de peso de um paciente com filtro de período | Must | GET `/api/v1/health/weight/?patient_id=1` → 200 paginado; `?from=...&to=...` filtra por `measured_at` |
| RF-02 | Criar log de peso com validação de faixa e data futura | Must | POST `/api/v1/health/weight/` com `patient_id`, `value_kg`, `measured_at` → 201; peso < 20 ou > 400 → 400; `measured_at` futuro → 400 |
| RF-03 | Deletar log de peso | Must | DELETE `/api/v1/health/weight/<id>/` → 204 |
| RF-04 | Listar/criar/deletar logs de sono (com `quality_score` 1–10) | Must | GET/POST/DELETE `/api/v1/health/sleep/` análogo; `quality_score` fora de 1–10 → 400 |
| RF-05 | Listar/criar/deletar logs de atividade (`duration_min` ≥ 1) | Must | GET/POST/DELETE `/api/v1/health/activity/`; `duration_min < 1` → 400 |
| RF-06 | Listar/criar/deletar notas de refeição (≤ 1000 chars) | Must | GET/POST/DELETE `/api/v1/health/nutrition/`; nota > 1000 → 400 |
| RF-07 | `patient_id` de outro médico ou inexistente → 404 | Must | Listar/criar com `patient_id` fora do escopo → 404 `NOT_FOUND` |
| RF-08 | Resumo biométrico de 7/30 dias | Should | GET `/api/v1/health/summary/?patient_id=1&window=30` → médias de sono, peso atual + tendência, total de atividade, últimas 3 notas |
| RF-09 | Persistência via chat (services `persist_*`) | Should | Chamadas de service com `patient_id` + dados válidos → log criado e metadados retornados |
| RF-10 | Edição de log não é permitida | Must | PUT/PATCH em qualquer ViewSet → 405 Method Not Allowed |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | `IsAuthenticated` como default global + autenticação JWT | `config/settings.py:116-119` (DEFAULT_AUTHENTICATION/PERMISSION) | 🟢 |
| Segurança | Ownership verificado no queryset e no `perform_create` | `apps/health_logs/views.py:19-24,45-52` | 🟢 |
| Segurança | Throttling global anon `30/min`, user `60/min`, chat `10/min` | `config/settings.py:123-127` | 🟢 |
| Desempenho | Índices compostos `(patient, -timestamp)` por tipo | `apps/health_logs/models.py:14,29,44,58` | 🟢 |
| Integridade | Validação de faixas plausíveis nos serializers (API) e services (chat) | `apps/health_logs/serializers.py`; `services/persist.py` | 🟢 |
| Privacidade | Dados biométricos removidos em cascata com o paciente/médico (LGPD) | `apps/health_logs/models.py` (`on_delete=CASCADE`) | 🟢 |

## Critérios de Aceitação

```gherkin
# Listagem — happy path
Dado um médico autenticado com um paciente de id 1 e 2 logs de peso
Quando faço GET em /api/v1/health/weight/?patient_id=1
Então recebo 200 paginado com 2 itens ordenados por -measured_at

# Listagem — sem patient_id
Quando faço GET em /api/v1/health/weight/
Então recebo 200 com lista vazia (queryset .none())

# Criação — validação de faixa
Dado um payload com value_kg=500
Quando faço POST em /api/v1/health/weight/
Então recebo 400 VALIDATION_ERROR indicando faixa 20–400 kg

# Criação — data futura
Dado um payload com measured_at no futuro
Quando faço POST em /api/v1/health/weight/
Então recebo 400 VALIDATION_ERROR

# Ownership
Dado um patient_id de outro médico
Quando faço GET em /api/v1/health/weight/?patient_id=99
Então recebo 404 NOT_FOUND

# Imutabilidade
Quando faço PATCH em /api/v1/health/weight/<id>/
Então recebo 405 Method Not Allowed

# Resumo — janela válida
Dado um paciente com dados na janela
Quando faço GET em /api/v1/health/summary/?patient_id=1&window=30
Então recebo 200 com avg_sleep_hours, latest_weight_kg, weight_trend_kg, total_activity_min e last_nutrition_notes

# Resumo — janela inválida
Quando faço GET em /api/v1/health/summary/?patient_id=1&window=90
Então recebo 200 com window_days=7 (fallback)
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| CRUD imutável dos 4 tipos (RF-01 a RF-06, RF-10) | Must | Caminho crítico de registro de dados biométricos |
| Ownership + validações de faixa (RF-07, RF-02) | Must | Integridade e privacidade (dados sensíveis) |
| Resumo agregado (RF-08) | Should | Apoia o chat/RAG, mas as anotações já trazem o peso mais recente |
| Persistência via chat (RF-09) | Should | Requisito do onboarding automático (ADR-004), com fallback (registro manual) |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/health_logs/models.py` | `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` | 🟢 |
| `apps/health_logs/views.py` | `_PatientQuerysetMixin`, 4 ViewSets, `health_summary`, `_get_patient_or_404` | 🟢 |
| `apps/health_logs/serializers.py` | `WeightLogSerializer`, `SleepLogSerializer`, `ActivityLogSerializer`, `NutritionNoteSerializer` | 🟢 |
| `apps/health_logs/urls.py` | router (weight/sleep/activity/nutrition) + `summary/` | 🟢 |
| `apps/health_logs/services/aggregate.py` | `summarize` | 🟢 |
| `apps/health_logs/services/persist.py` | `persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` | 🟢 |
| `config/settings.py` | default auth/permission/throttle/pagination | 🟢 |

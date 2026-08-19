# Health Logs / CRUD de Logs, Design Técnico

> Contrato operacional de **COMO** o CRUD de logs é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/health/weight/` | `?patient_id=&from=&to=` | lista | 200, 401 | `IsAuthenticated` |
| POST | `/api/v1/health/weight/` | `{patient_id, value_kg, measured_at}` | log | 201, 400, 404, 401 | `IsAuthenticated` |
| DELETE | `/api/v1/health/weight/<id>/` | — | 204 | 204, 404, 401 | `IsAuthenticated` |

> O mesmo contrato vale para `sleep/`, `activity/` e `nutrition/` com campos específicos.

## Fluxo Principal

1. **GET:** exige `patient_id` (ausente → queryset vazio); valida ownership; filtra `patient_id`; aplica `from`/`to` via `__gte`/`__lte`. (`apps/health_logs/views.py`) 🟢
2. **POST:** exige `patient_id` no body (ausente → 400 "patient_id é obrigatório"); valida ownership (404); valida serializer; salva com `patient_id` fixado. (`views.py`) 🟢
3. **DELETE:** queryset restrito ao paciente do dono; pk de outro → 404; sucesso → 204. (`views.py`) 🟢

## Fluxos Alternativos

- **[Valor fora da faixa — HTTP]:** `ValidationError` por tipo via serializer: peso 20–400; sono apenas `quality_score` 1–10; atividade apenas `duration_min ≥ 1` (`type` obrigatório por default DRF); nutrição apenas ≤1000 chars. As faixas de horas do sono, truncamento de `type` (40) e mínimo de 10 chars da nutrição são validados **apenas na via chat** (`services/persist.py`). 🟡 [Revisão Codex]
- **[Timestamp futuro — HTTP]:** rejeitado **apenas no peso** (`validate_measured_at` do `WeightLogSerializer`). Sono/atividade/nutrição não validam timestamp futuro no HTTP — só na via chat (`services/persist.py`). 🟡 [Revisão Codex]

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.patients.models.Patient` | Ownership | `filter(doctor=request.user)` |
| `apps.common.exceptions.AppError` | 404 uniforme | `NOT_FOUND` |
| `apps.common.permissions.IsAuthenticated` (default) | Proteção | `permission_classes` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| ViewSets por tipo de log (um endpoint por recurso) | `views.py` | 🟢 |
| `patient_id` explícito (query/body) em vez de path param | `views.py` | 🟢 |
| 404 para ownership (anti-reconhecimento) | `views.py` | 🟢 |
| Validação de faixa no serializer (não no model) | `serializers.py` | 🟢 |

## Riscos e Lacunas

- 🟡 GET sem `patient_id` retorna lista vazia (200) em vez de 400 — comportamento ambíguo.
- 🟢 Isolamento entre pacientes confirmado (testes em `tests/health_logs/test_summary.py`).

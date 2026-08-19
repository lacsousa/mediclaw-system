# Health Logs / persist_weight_log, Design Técnico

> Contrato operacional de **COMO** a persistência via captura é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `persist_weight_log` | `(patient_id: int, data: dict) -> dict` | `{id, value_kg, measured_at}` | Sem HTTP; usado no `user_data_capture` |
| `persist_sleep_log` | `(patient_id: int, data: dict) -> dict` | `{id, ...}` | hours/quality |
| `persist_activity_log` | `(patient_id: int, data: dict) -> dict` | `{id, ...}` | duration_min/type |
| `persist_nutrition_note` | `(patient_id: int, data: dict) -> dict` | `{id, ...}` | note 10–1000 |

## Fluxo Principal

1. `value_kg = float(data["value_kg"])` — conversão do texto capturado. (`services/persist.py`) 🟢
2. Valida `20 ≤ value_kg ≤ 400`; falha → `ValidationError`. (`persist.py`) 🟢
3. `measured_at = data.get("measured_at") or timezone.now()`; rejeita futuro. (`persist.py`) 🟢
4. `WeightLog.objects.create(patient_id=patient_id, value_kg=..., measured_at=...)`. (`persist.py`) 🟢
5. Retorna `{id, value_kg, measured_at}`. (`persist.py`) 🟢

## Fluxos Alternativos

- **[Valor inválido no `float`]:** exceção de conversão → captura não persiste. 🟡
- **[Campos datetime ausentes]:** default `timezone.now()` para todos os tipos. 🟢
- **[Demais tipos]:** regras próprias (RN-03 a RN-05) no mesmo padrão. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.health_logs.models` | Persistência | `WeightLog.objects.create` |
| `rest_framework` | Erros de validação | `ValidationError` |
| `apps.ai_engine.services.user_data_capture` | Caller | Captura → chama os `persist_*` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Validação no service (não no serializer) pois não há HTTP | `persist.py` | 🟢 |
| Default `timezone.now()` para timestamps ausentes | `persist.py` | 🟢 |
| Regex do chat capturam valor, mas não datetime — LLM preenche | `capture_rules.py`; `persist.py` | 🟢 |

## Riscos e Lacunas

- 🟡 Falha de conversão de `float` não tratada explicitamente (exceção crua).
- 🟢 Sem PII em logs — metadados apenas.

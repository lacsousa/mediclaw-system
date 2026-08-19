# Health Logs / Summary, Design Técnico

> Contrato operacional de **COMO** o resumo é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/health/summary/` | `?patient_id=&window=` | resumo JSON | 200, 400, 404, 401 | `IsAuthenticated` |

## Fluxo Principal

1. Valida `patient_id` (ausente → 400) e ownership (404). (`apps/health_logs/views.py:87`) 🟢
2. Resolve `window`: `7`/`30` ou default `7`. (`views.py`) 🟢
3. `summarize(patient_id, window)` computa:
   - `avg` de sono + qualidade na janela. (`services/aggregate.py`) 🟢
   - `latest_weight` (sem janela) e `first_weight` na janela → `weight_trend`. (`aggregate.py`) 🟢
   - `total` de atividade na janela. (`aggregate.py`) 🟢
   - top-3 notas por `logged_at`. (`aggregate.py`) 🟢
4. Retorna `200` resumo JSON. 🟢

## Fluxos Alternativos

- **[Sem logs na janela]:** campos de janela vazios/nulos; `latest_weight` ainda pode existir. 🟡
- **[`window` inválido]:** default `7` (sem erro). 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.health_logs.models` | Agregação | `avg`, `sum`, ordenação por timestamp |
| `apps.patients.models.Patient` | Ownership | `filter(doctor=request.user)` |
| `apps.ai_engine.skills.health_summary` | Reuso da agregação | delega para `summarize` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| `latest_weight` sem janela, `first` na janela para tendência | `aggregate.py` | 🟢 |
| Janela default 7 com aceite de 30 | `views.py` | 🟢 |
| `summarize` compartilhado entre endpoint e skill do LLM | `aggregate.py`; `skills/health_summary.py` | 🟢 |

## Riscos e Lacunas

- 🟡 Médias de sono ignoram logs sem `hours`/`quality` — validar tratamento de nulos.
- 🟢 Testes em `tests/health_logs/test_summary.py` cobrem summary, validação de peso e isolamento entre pacientes.

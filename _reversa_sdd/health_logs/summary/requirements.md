# Health Logs / Summary — Requisitos

> Contrato operacional do caso de uso **Resumo agregado** (`GET /api/v1/health/summary/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Retorna um resumo agregado de saúde de um paciente para uma janela (padrão 7 dias, opcional 30): média de sono e qualidade do sono, tendência de peso (último − primeiro na janela), total de atividade e top-3 notas de nutrição.

## Regras de Negócio

- **RN-01** — `patient_id` obrigatório; ausente → 400 `VALIDATION_ERROR`. 🟢
- **RN-02** — Ownership: paciente de outro médico → 404 `NOT_FOUND`. 🟢
- **RN-03** — `window` aceito: `7` ou `30`; qualquer outro/ausente → default `7`. 🟢
- **RN-04** — `latest_weight` calculado **sem** janela (último peso geral); `weight_trend = latest − first` (first na janela). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Resumo com sono, peso, atividade e nutrição | Must | GET `/api/v1/health/summary/?patient_id=1&window=7` → 200 com métricas |
| RF-02 | Validação de `patient_id` e ownership | Must | Sem `patient_id` → 400; paciente de outro médico → 404 |
| RF-03 | Default de janela | Must | `window` ausente/outro → usa 7 dias |

## Critérios de Aceitação

```gherkin
Dado um paciente próprio com logs de sono, peso, atividade e nutrição
Quando faço GET em /api/v1/health/summary/?patient_id=1&window=7
Então recebo 200 com avg de sono/qualidade, weight_trend, total de atividade e top-3 notas

Dado um GET sem patient_id
Quando faço GET em /api/v1/health/summary/
Então recebo 400 VALIDATION_ERROR

Dado um patient_id de outro médico
Quando faço GET em /api/v1/health/summary/
Então recebo 404 NOT_FOUND

Dado um window ausente ou inválido
Quando faço GET em /api/v1/health/summary/?patient_id=1
Então o resumo usa a janela padrão de 7 dias
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/health_logs/views.py:87` | `health_summary` | 🟢 |
| `apps/health_logs/services/aggregate.py` | `summarize` | 🟢 |
| `apps/ai_engine/skills/health_summary.py` | delegação para `summarize` | 🟢 |

# Health Logs / Summary, Tarefas de Implementação

> Sequência executável para reimplementar o resumo a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos de logs de saúde (weight, sleep, activity, nutrition)
- [ ] Modelo `Patient`

## Tarefas

- [ ] **T-01**, Service `summarize` com agregações por janela
  - Origem no legado: `apps/health_logs/services/aggregate.py`
  - Critério de pronto: avg de sono/qualidade na janela; `latest_weight` sem janela; `first_weight` na janela → `weight_trend`; total de atividade; top-3 notas por `logged_at`
  - Confiança: 🟢

- [ ] **T-02**, View `health_summary` com validação e default de janela
  - Origem no legado: `apps/health_logs/views.py:87`
  - Critério de pronto: `patient_id` obrigatório (400) e ownership (404); `window` 7/30 ou default 7
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Resumo happy path → 200 com todas as métricas
- [ ] **TT-02**, Sem `patient_id` → 400; paciente de outro médico → 404
- [ ] **TT-03**, `window` ausente → default 7 dias

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 a TT-03.

## Lacunas Pendentes (🔴)

- [ ] Definir tratamento de nulos nas médias (logs sem `hours`/`quality`).

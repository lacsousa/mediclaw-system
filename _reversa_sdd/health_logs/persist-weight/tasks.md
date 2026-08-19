# Health Logs / persist_weight_log, Tarefas de Implementação

> Sequência executável para reimplementar a persistência via captura a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote`

## Tarefas

- [ ] **T-01**, `persist_weight_log` com validação de faixa e timestamp
  - Origem no legado: `apps/health_logs/services/persist.py`
  - Critério de pronto: `float` do valor; 20–400 senão `ValidationError`; `measured_at` default `now`, rejeita futuro; cria `WeightLog` e retorna `{id, value_kg, measured_at}`
  - Confiança: 🟢

- [ ] **T-02**, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` seguindo o padrão
  - Origem no legado: `apps/health_logs/services/persist.py`
  - Critério de pronto: regras RN-03 a RN-05 implementadas (sono hours/quality, atividade duration/type, nutrição len)
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Peso válido → `WeightLog` criado com `{id, value_kg, measured_at}`
- [ ] **TT-02**, Peso fora de 20–400 → `ValidationError`
- [ ] **TT-03**, `measured_at` futuro → `ValidationError`
- [ ] **TT-04**, Regras de sono/atividade/nutrição

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 a TT-04.

## Lacunas Pendentes (🔴)

- [ ] Tratar conversão de `float` com erro controlado (hoje exceção crua).

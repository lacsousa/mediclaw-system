# Health Logs / CRUD de Logs, Tarefas de Implementação

> Sequência executável para reimplementar o CRUD de logs a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` com FK `patient`
- [ ] Modelo `Patient` com FK `doctor`

## Tarefas

- [ ] **T-01**, ViewSets de weight/sleep/activity/nutrition com ownership
  - Origem no legado: `apps/health_logs/views.py`
  - Critério de pronto: `patient_id` obrigatório; ownership → 404; GET com `from`/`to`; DELETE restrito ao paciente
  - Confiança: 🟢

- [ ] **T-02**, Serializers com validação de faixa por tipo
  - Origem no legado: `apps/health_logs/serializers.py`
  - Critério de pronto: peso 20–400 e `measured_at` não-futuro; sono 0<h≤24 e quality 1–10; atividade `duration_min≥1` e `type` ≤40; nutrição 10–1000 chars
  - Confiança: 🟢

- [ ] **T-03**, Rotas `/api/v1/health/{weight,sleep,activity,nutrition}/`
  - Origem no legado: `apps/health_logs/urls.py`
  - Critério de pronto: rotas montadas, `IsAuthenticated`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, POST peso válido → 201; peso fora de 20–400 → 400
- [ ] **TT-02**, POST sem `patient_id` → 400; `patient_id` de outro médico → 404
- [ ] **TT-03**, GET com `from`/`to` → apenas logs na janela
- [ ] **TT-04**, DELETE do próprio paciente → 204; de outro → 404
- [ ] **TT-05**, Validações de sono/atividade/nutrição conforme regras

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-05.

## Lacunas Pendentes (🔴)

- [ ] Decidir se GET sem `patient_id` deve retornar 400 em vez de lista vazia.

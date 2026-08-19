# Health Logs / persist_weight_log — Requisitos

> Contrato operacional do caso de uso **Persistência de log via captura no chat** (`apps/health_logs/services/persist.py`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Service chamado pelo orquestrador de IA (`user_data_capture`) para gravar logs biométricos capturados no chat. `persist_weight_log` valida peso e timestamp e persiste. O mesmo padrão vale para `persist_sleep_log`, `persist_activity_log` e `persist_nutrition_note`.

## Regras de Negócio

- **RN-01** — `value_kg` convertido com `float`; faixa `20 ≤ value ≤ 400`. 🟢
- **RN-02** — `measured_at` padrão `timezone.now()` quando ausente; não pode ser futuro. 🟢
- **RN-03** — São: `0 < hours ≤ 24`, `quality` 1–10 default 5. 🟢
- **RN-04** — Atividade: `duration_min ≥ 1`, `type` obrigatório/truncado em 40. 🟢
- **RN-05** — Nutrição: `10 ≤ len(note) ≤ 1000`. 🟢
- **RN-06** — Falha de validação lança `ValidationError` (o chat trata como dado não persistível). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Persistir peso capturado | Must | `persist_weight_log(patient_id, {"value_kg": "75.5", ...})` → `WeightLog` criado e `{id, value_kg, measured_at}` retornado |
| RF-02 | Validar faixa e timestamp | Must | Peso fora de 20–400 ou `measured_at` futuro → `ValidationError` |
| RF-03 | Persistir demais tipos seguindo o padrão | Should | `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` com suas regras |

## Critérios de Aceitação

```gherkin
Dado um patient_id válido e data de peso "75.5"
Quando chamo persist_weight_log(patient_id, data)
Então um WeightLog é criado e retorna {id, value_kg: 75.5, measured_at}

Dado value_kg = "500" (fora de 20-400)
Quando chamo persist_weight_log(patient_id, data)
Então é lançado ValidationError

Dado measured_at no futuro
Quando chamo persist_weight_log(patient_id, data)
Então é lançado ValidationError
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/health_logs/services/persist.py` | `persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` | 🟢 |
| `apps/ai_engine/services/user_data_capture.py` | caller (captura) | 🟢 |
| `apps/health_logs/models.py` | modelos de log | 🟢 |

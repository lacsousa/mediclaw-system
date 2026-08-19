# Health Logs / CRUD de Logs Biométricos — Requisitos

> Contrato operacional do caso de uso **CRUD de logs por tipo** (GET/POST/DELETE em `/api/v1/health/{weight,sleep,activity,nutrition}/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Cria, lista e deleta logs biométricos (peso, sono, atividade, nutrição) de um paciente, escopados ao médico dono via `patient_id` (query param no GET, body no POST). Inclui validações de faixa por tipo e isolamento entre médicos.

## Regras de Negócio

- **RN-01** — `patient_id` no POST é obrigatório (ausente → 400 VALIDATION_ERROR); no GET, ausente → 200 lista vazia (`.none()`, **não** é erro). 🟢 [Revisão Codex]
- **RN-02** — Ownership: paciente de outro médico → `404 NOT_FOUND` (não 403). 🟢
- **RN-03** — Peso: `20 ≤ value_kg ≤ 400`; `measured_at` não pode ser futuro — únicos validadores de faixa+temporalidade do HTTP. 🟢
- **RN-04** — Sono (HTTP): apenas `quality_score` 1–10 é validado (default 5). Faixa `0 < duration_hours ≤ 24` é validada **só na via chat** (`services/persist.py`). 🟡 [Revisão Codex]
- **RN-05** — Atividade (HTTP): `duration_min ≥ 1`; `type` obrigatório (default DRF). Truncamento em 40 chars é **só na via chat** (`services/persist.py`). 🟡 [Revisão Codex]
- **RN-06** — Nutrição (HTTP): apenas `len(note) ≤ 1000` é validado. Mínimo de 10 chars é **só na via chat** (`services/persist.py`). 🟡 [Revisão Codex]
- **RN-07** — DELETE restringe o queryset ao paciente; pk de outro → 404. 🟢
- **RN-08** — GET com `from`/`to` filtra timestamps por `__gte`/`__lte`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Listar logs por tipo e paciente com filtro de janela | Must | GET `/api/v1/health/weight/?patient_id=1&from=&to=` → 200 lista filtrada |
| RF-02 | Criar log com validação de faixa | Must | POST `/api/v1/health/weight/` `{patient_id, value_kg, measured_at}` → 201 |
| RF-03 | Deletar log restrito ao paciente | Must | DELETE `/api/v1/health/weight/<id>/` do próprio paciente → 204 |
| RF-04 | Bloquear acesso a paciente de outro médico | Must | GET/POST/DELETE com `patient_id` de outro médico → 404 |

## Critérios de Aceitação

```gherkin
Dado um médico autenticado com paciente próprio
Quando faço POST em /api/v1/health/weight/ com {patient_id, value_kg: 75.5, measured_at: "2026-08-01"}
Então recebo 201 com o log criado

Dado um POST sem patient_id ou com value_kg fora de 20-400
Quando faço POST em /api/v1/health/weight/
Então recebo 400 VALIDATION_ERROR

Dado um patient_id de outro médico
Quando faço GET/POST/DELETE em /api/v1/health/weight/
Então recebo 404 NOT_FOUND

Dado um GET com patient_id próprio e from/to
Quando faço GET em /api/v1/health/weight/?patient_id=1&from=2026-07-01&to=2026-07-31
Então recebo apenas os logs na janela
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/health_logs/views.py` | viewsets de weight/sleep/activity/nutrition | 🟢 |
| `apps/health_logs/serializers.py` | validadores de faixa por tipo | 🟢 |
| `apps/health_logs/models.py` | `WeightLog`, `SleepLog`, `ActivityLog`, `NutritionNote` | 🟢 |
| `apps/health_logs/urls.py` | rotas `/api/v1/health/...` | 🟢 |

# User Stories — Logs de Saúde

> Fluxo: registro e consulta de logs biométricos (peso, sono, atividade, nutrição) e resumo.
> Cobertura: módulo `health_logs`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-HL-01 — Registrar log biométrico

**Como** médico,
**quero** registrar peso, sono, atividade e refeições de um paciente,
**para** acompanhar seus dados ao longo do tempo.

- Critérios de aceite:
  - POST `/api/v1/health/{weight|sleep|activity|nutrition}/` → 201 log criado.
  - Log vinculado ao `patient_id`; paciente inexistente → 404.
  - Payload inválido → 400 `VALIDATION_ERROR`. 🟢

## US-HL-02 — Listar e gerenciar logs

**Como** médico,
**quero** listar, editar e excluir os logs de um paciente,
**para** corrigir registros equivocados.

- Critérios de aceite:
  - ViewSets por tipo (`/weight/`, `/sleep/`, `/activity/`, `/nutrition/`) com CRUD completo (GET/POST/PUT/PATCH/DELETE). 🟢
  - Queryset filtrado ao paciente do médico logado. 🟢

## US-HL-03 — Ver resumo de saúde

**Como** médico,
**quero** obter um resumo agregado (tendências, IMC),
**para** contextualizar a recomendação da IA.

- Critérios de aceite:
  - GET `/api/v1/health/summary/` com `patient_id` e janela (`window`, default 7) → resumo agregado.
  - Consumido pelo orquestrador (`health_summary`) no system prompt. 🟢

## US-HL-04 — Captura automática (persistência)

**Como** sistema,
**quero** persistir peso, sono, atividade e nutrição mencionados no chat,
**para** manter o perfil do paciente sem digitação manual.

- Critérios de aceite:
  - Serviços `persist_weight_log`, `persist_sleep_log`, `persist_activity_log`, `persist_nutrition_note` chamados pela captura automática (ver US-IA-04). 🟢
  - Erros de validação viram `CaptureResult.errors`, sem quebrar o turno. 🟢

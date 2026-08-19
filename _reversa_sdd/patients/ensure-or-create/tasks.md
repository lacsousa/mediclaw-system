# Patients / ensure_or_create_patient, Tarefas de Implementação

> Sequência executável para reimplementar a captura de paciente a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos `Patient` e `Conversation`

## Tarefas

- [ ] **T-01**, Service `ensure_or_create_patient` com reuso/preenchimento do tentativo
  - Origem no legado: `apps/patients/services/patient.py`
  - Critério de pronto: conversa sem paciente → cria e vincula (`conv.title` = nome); com paciente vazio → preenche; com paciente nomeado → retorna sem duplicar; grava com `update_fields`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Conversa sem paciente → cria e vincula, título = nome
- [ ] **TT-02**, Paciente tentativo com nome vazio → preenche e reutiliza
- [ ] **TT-03**, Conversa já com paciente nomeado → sem duplicação

## Ordem Sugerida

1. T-01, testes TT-01 a TT-03.

## Lacunas Pendentes (🔴)

- [ ] Confirmar metadados do log `patient_created` (correlação `conversation_id`/`patient_id`).

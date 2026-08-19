# Patients / resolve_patient_dob, Tarefas de Implementação

> Sequência executável para reimplementar o dedup por DOB a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelos `Patient` e `Conversation`; constraint parcial `unique_patient_name_dob_per_doctor`

## Tarefas

- [ ] **T-01**, Service `resolve_patient_dob` com dedup e merge
  - Origem no legado: `apps/patients/services/patient.py`
  - Critério de pronto: conversa sem paciente → `None`; sem duplicata → atualiza `birth_date`; com duplicata e tentativo sem dados → re-vincula + deleta tentativo; com dados → re-vincula + mantém; loga `patient_merged`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Sem duplicata → `birth_date` atualizado e paciente retornado
- [ ] **TT-02**, Duplicata sem dados no tentativo → re-vínculo + deleção do tentativo
- [ ] **TT-03**, Duplicata com dados no tentativo → re-vínculo + tentativo preservado
- [ ] **TT-04**, Conversa sem paciente → `None`

## Ordem Sugerida

1. T-01, testes TT-01 a TT-04.

## Lacunas Pendentes (🔴)

- [ ] Definir parsing/normalização de `birth_date` capturada no chat (formatos variados).

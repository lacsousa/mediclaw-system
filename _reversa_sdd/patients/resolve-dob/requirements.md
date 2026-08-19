# Patients / resolve_patient_dob — Requisitos

> Contrato operacional do caso de uso **Dedup por data de nascimento** (`apps/patients/services/patient.py`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Service chamado pelo orquestrador quando o chat captura a data de nascimento de um paciente. Deduplica pacientes do mesmo médico com mesmo nome + DOB: reutiliza o existente e, se o paciente tentativo não tiver dados biométricos/refeições, deleta-o. Garante a unicidade `(doctor, first_name, birth_date)` na prática.

## Regras de Negócio

- **RN-01** — Se `conv.patient_id` é nulo, retorna `None` (sem paciente para deduplicar). 🟢
- **RN-02** — Busca paciente do mesmo médico com `first_name__iexact` + `birth_date` igual, excluindo o atual. 🟢
- **RN-03** — Não encontrou existente → atualiza `birth_date` no paciente atual e retorna. 🟢
- **RN-04** — Encontrou existente e o tentativo **não** tem logs/refeições → re-vincula a conversa ao existente e deleta o tentativo. 🟢
- **RN-05** — Encontrou existente e o tentativo **tem** dados → re-vincula a conversa ao existente, mantém o tentativo. 🟢
- **RN-06** — Loga `patient_merged` quando ocorre merge. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Resolver DOB atualizando o paciente atual | Must | Sem duplicata → `birth_date` do paciente atual atualizado |
| RF-02 | Deduplicar paciente existente sem dados no tentativo | Must | Mesmo nome + DOB → conversa re-vinculada ao existente, tentativo deletado |
| RF-03 | Deduplicar mantendo tentativo com dados | Should | Tentativo com logs/refeições → conversa re-vinculada ao existente, tentativo preservado |

## Critérios de Aceitação

```gherkin
Dado uma conversa com paciente tentativo sem birth_date e sem duplicata
Quando chamo resolve_patient_dob(conv_id, doctor_id, "1990-01-01")
Então o birth_date do paciente atual é atualizado e ele é retornado

Dado um paciente existente (mesmo médico) com first_name e birth_date iguais, e tentativo sem dados
Quando chamo resolve_patient_dob(conv_id, doctor_id, birth_date)
Então a conversa re-vincula ao existente e o tentativo é deletado

Dado um paciente existente duplicado e tentativo com logs/refeições
Quando chamo resolve_patient_dob(conv_id, doctor_id, birth_date)
Então a conversa re-vincula ao existente e o tentativo é mantido

Dado uma conversa sem paciente
Quando chamo resolve_patient_dob(conv_id, doctor_id, birth_date)
Então retorna None
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/patients/services/patient.py` | `resolve_patient_dob` | 🟢 |
| `apps/patients/models.py` | constraint parcial `unique_patient_name_dob_per_doctor` | 🟢 |
| `apps/conversations/models.py` | `Conversation.patient` | 🟢 |

# Patients / ensure_or_create_patient — Requisitos

> Contrato operacional do caso de uso **Captura de paciente via chat** (`apps/patients/services/patient.py`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Service chamado pelo orquestrador de IA quando o chat captura o nome de um paciente. Cria o paciente vinculado à conversa (se a conversa ainda não tiver um) ou preenche o `first_name` de um paciente tentativo com nome vazio. Atualiza o título da conversa com o nome do paciente.

## Regras de Negócio

- **RN-01** — Cada conversa mantém um único paciente tentativo; se `conv.patient_id` já existe, não cria outro. 🟢
- **RN-02** — Se o paciente da conversa tem `first_name` vazio, apenas preenche o nome e salva. 🟢
- **RN-03** — Ao criar, `first_name` é o nome capturado após `strip`; `conv.title` recebe o nome (limitado a 120). 🟢
- **RN-04** — A gravação usa `update_fields=["patient", "title", "updated_at"]`. 🟢
- **RN-05** — Loga `patient_created` (debug) quando cria; metadados sem PII. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Criar paciente e vincular à conversa | Must | `ensure_or_create_patient(conversation_id, doctor_id, "Ana")` → paciente criado, `conv.patient` apontando, `conv.title` = nome |
| RF-02 | Preencher nome de paciente tentativo | Must | Conversa com paciente de `first_name` vazio → preenche e retorna o mesmo paciente |
| RF-03 | Reutilizar paciente já vinculado | Must | Conversa já com paciente nomeado → retorna sem criar |

## Critérios de Aceitação

```gherkin
Dado uma conversa sem paciente
Quando chamo ensure_or_create_patient(conv_id, doctor_id, "Ana")
Então um Patient é criado com first_name "Ana", vinculado à conversa, e conv.title = "Ana"

Dado uma conversa com paciente de first_name vazio
Quando chamo ensure_or_create_patient(conv_id, doctor_id, "Ana")
Então o first_name é preenchido e o mesmo paciente é retornado

Dado uma conversa com paciente nomeado "Ana"
Quando chamo ensure_or_create_patient(conv_id, doctor_id, "Ana")
Então o paciente existente é retornado sem duplicação
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/patients/services/patient.py` | `ensure_or_create_patient` | 🟢 |
| `apps/conversations/models.py` | `Conversation.patient`, `title` | 🟢 |
| `apps/ai_engine/` | caller (captura de dados) | 🟡 |

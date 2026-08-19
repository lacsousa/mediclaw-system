# Patients / ensure_or_create_patient, Design Técnico

> Contrato operacional de **COMO** a captura de paciente é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `ensure_or_create_patient` | `(conversation_id: int, doctor_id: int, first_name: str) -> Patient` | `Patient` | Sem HTTP; usado na captura via chat |

## Fluxo Principal

1. `conv = Conversation.objects.get(pk=conversation_id)`. (`services/patient.py`) 🟢
2. Se `conv.patient_id` existe: se `patient.first_name` vazio, preenche e `save`; retorna o paciente. (`patient.py`) 🟢
3. Senão, cria `Patient.objects.create(doctor_id=doctor_id, first_name=first_name.strip())`. (`patient.py`) 🟢
4. `conv.patient = patient`; `conv.title = first_name[:120]`. (`patient.py`) 🟢
5. `conv.save(update_fields=["patient", "title", "updated_at"])`. (`patient.py`) 🟢
6. `logger.debug("patient_created")` e retorna o paciente. (`patient.py`) 🟢

## Fluxos Alternativos

- **[Paciente já nomeado]:** retorna sem criar/alterar. (`patient.py`) 🟢
- **[Conversa inexistente]:** `Conversation.DoesNotExist` propaga. 🟡

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.patients.models.Patient` | Alvo da criação | `Patient.objects.create(doctor_id, first_name)` |
| `apps.conversations.models.Conversation` | Vínculo | `conv.patient`, `conv.title` |
| `apps.common.logging_config.get_logger` | Log estruturado | `logger.debug("patient_created")` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Um paciente tentativo por conversa | `patient.py` | 🟢 |
| Escrita mínima via `update_fields` | `patient.py` | 🟢 |
| Título da conversa espelha o nome do paciente | `patient.py` | 🟢 |
| Log `patient_created` com metadados, sem PII | `patient.py` | 🟢 |

## Riscos e Lacunas

- 🔴 Log `patient_created` não inclui `patient_id`/`conversation_id` confirmado nesta leitura — validar se a correlação é logada.
- 🟡 Unicidade é tratada na aplicação; no banco apenas via constraint parcial `(doctor, first_name, birth_date)`.

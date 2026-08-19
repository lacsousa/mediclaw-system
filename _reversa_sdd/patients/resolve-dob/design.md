# Patients / resolve_patient_dob, Design Técnico

> Contrato operacional de **COMO** o dedup por DOB é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `resolve_patient_dob` | `(conversation_id: int, doctor_id: int, birth_date: date) -> Patient \| None` | `Patient \| None` | Sem HTTP; usado na captura via chat |

## Fluxo Principal

1. `conv = Conversation.objects.get(pk=conversation_id)`; se `conv.patient_id` é nulo → retorna `None`. (`services/patient.py`) 🟢
2. Busca duplicata: `Patient.objects.filter(doctor_id=doctor_id, first_name__iexact=conv.patient.first_name, birth_date=birth_date).exclude(pk=conv.patient_id)`. (`patient.py`) 🟢
3. Sem duplicata → atualiza `birth_date` no paciente atual e retorna. (`patient.py`) 🟢
4. Com duplicata:
   - Se tentativo **não** tem logs/refeições → `conv.patient = existente`; `save`; `tentativo.delete()`. (`patient.py`) 🟢
   - Se tentativo **tem** dados → `conv.patient = existente`; `save`; mantém tentativo. (`patient.py`) 🟢
5. `logger.debug("patient_merged")` e retorna o existente. (`patient.py`) 🟢

## Fluxos Alternativos

- **[Conversa sem paciente]:** retorna `None` — sem ação. (`patient.py`) 🟢
- **[Tentativo com dados]:** merge preserva o tentativo (dados não são perdidos, apenas desvinculados da conversa). (`patient.py`) 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.patients.models.Patient` | Busca/merge | `filter(...).exclude(...)` |
| `apps.conversations.models.Conversation` | Re-vínculo | `conv.patient = existente` |
| `apps.health_logs` / `nutrition` | Verificação de dados do tentativo | Logs/refeições existentes |
| `apps.common.logging_config.get_logger` | Log estruturado | `logger.debug("patient_merged")` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Merge só quando há nome + DOB iguais do mesmo médico | `patient.py` | 🟢 |
| Tentativo preservado se tiver dados (anti-perda de saúde) | `patient.py` | 🟢 |
| Unicidade também garantida no banco por constraint parcial | `models.py:24-30` | 🟢 |

## Riscos e Lacunas

- 🟡 Comparação de `first_name` é `iexact` — variações de acento/grafia podem não deduplicar.
- 🟡 DOB capturada pode chegar em formatos variados — validar parsing antes de gravar.

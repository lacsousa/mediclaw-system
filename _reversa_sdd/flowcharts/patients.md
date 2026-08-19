# Fluxogramas — patients

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. Listar pacientes (GET `/api/v1/patients/`)

```mermaid
flowchart TD
    A[GET /patients] --> B[filter doctor=request.user]
    B --> C[_annotate_patients]
    C --> C1[conversation_count: Count não-deletadas]
    C --> C2[last_seen_at: Max updated_at não-deletadas]
    C --> C3[latest_weight_kg: Subquery top-1 por measured_at]
    C --> D[total = count]
    C --> E[items = qs[offset:offset+20]]
    E --> F{offset+20 < total?}
    F -- sim --> G[next = ?page=+1]
    F -- não --> H[next = null]
    D --> I[200 results + count + next]
```

## 2. Detalhe / edição / exclusão (GET/PATCH/DELETE `/api/v1/patients/<id>/`)

```mermaid
flowchart TD
    A[Request <id> autenticado] --> B[busca patient com doctor=request.user]
    B --> C{existe?}
    C -- não --> C1[404 NOT_FOUND]
    C -- sim --> D{Método?}
    D -- GET --> D1[200 PatientDetail + logs + conversas]
    D -- PATCH --> E{PatientListSerializer partial válido?}
    E -- não --> E1[400 VALIDATION_ERROR]
    E -- sim --> F[save]
    F --> G[200 PatientListSerializer]
    D -- DELETE --> H[patient.delete cascade]
    H --> I[204 No Content]
```

## 3. ensure_or_create_patient (captura de nome via chat)

```mermaid
flowchart TD
    A[ensure_or_create conv_id, doctor_id, first_name] --> B[get Conversation]
    B --> C{conv.patient_id existe?}
    C -- sim --> D{patient.first_name vazio?}
    D -- sim --> E[preenche first_name, save]
    D -- não --> F[retorna patient]
    E --> F
    C -- não --> G[Patient.create doctor_id + first_name.trim]
    G --> H[conv.patient = patient; conv.title = name[:120]]
    H --> I[save update_fields patient/title/updated_at]
    I --> J[logger.debug patient_created]
    J --> F
```

## 4. resolve_patient_dob (dedup ao capturar DOB)

```mermaid
flowchart TD
    A[resolve_patient_dob conv_id, doctor_id, birth_date] --> B[get Conversation]
    B --> C{conv.patient_id é null?}
    C -- sim --> C1[return null]
    C -- não --> D[busca Patient com mesmo first_name iexact + birth_date, exclude self]
    D --> E{encontrou?}
    E -- não --> E1[atualiza birth_date no tentativo]
    E1 --> E2[return patient]
    E -- sim --> F{tentativo tem logs/nutrition?}
    F -- não --> F1[re-vincula conv ao existente + deleta tentativo]
    F -- sim --> F2[re-vincula conv ao existente, mantém tentativo]
    F1 --> G[logger.debug patient_merged]
    F2 --> H[return existente]
    G --> H
```

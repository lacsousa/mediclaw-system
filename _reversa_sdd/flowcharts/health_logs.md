# Fluxogramas — health_logs

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. CRUD via Viewset (GET/POST/DELETE — ex.: weight)

```mermaid
flowchart TD
    A[Request autenticado] --> B{GET/POST/DELETE}
    B -- GET --> C{patient_id query param?}
    C -- não --> C1[queryset vazio]
    C -- sim --> D[valida ownership patient_id]
    D --> D1{é do médico?}
    D1 -- não --> D2[404 NOT_FOUND]
    D1 -- sim --> E[filter patient_id]
    E --> F{from/to?}
    F -- sim --> G[filter ts __gte/__lte]
    F -- não --> H[200 lista]
    G --> H
    B -- POST --> I{patient_id no body?}
    I -- não --> I1[400 patient_id obrigatório]
    I -- sim --> J[valida ownership]
    J -- não --> J1[404 NOT_FOUND]
    J -- sim --> K{Serializer válido?}
    K -- não --> K1[400 VALIDATION_ERROR]
    K -- sim --> L[save patient_id=...]
    L --> M[201]
    B -- DELETE --> N[qs restrita ao paciente; pk de outro -> 404]
    N --> O[204]
```

**Validações de serializer:** peso 20–400 🟢 · `measured_at` não futuro 🟢 · quality 1–10 🟢 · duration_min ≥ 1 🟢 · note ≤ 1000 🟢

## 2. Summary (GET `/api/v1/health/summary/`)

```mermaid
flowchart TD
    A[GET summary] --> B{patient_id?}
    B -- não --> B1[400 VALIDATION_ERROR]
    B -- sim --> C[valida ownership]
    C -- não --> C1[404 NOT_FOUND]
    C -- sim --> D{window?}
    D -- 7/30 --> E[usar window]
    D -- outro/ausente --> E2[window = 7]
    E --> F[summarize patient_id, window]
    E2 --> F
    F --> F1[avg sono + qualidade na janela]
    F --> F2[latest_weight sem janela]
    F --> F3[first_weight na janela]
    F --> F4[total atividade na janela]
    F --> F5[top-3 notas por logged_at]
    F1 --> G[weight_trend = latest - first]
    F2 --> G
    F3 --> G
    F4 --> H[200 resumo JSON]
    F5 --> H
    G --> H
```

## 3. persist_weight_log (captura via chat — user_data_capture)

```mermaid
flowchart TD
    A[persist_weight_log patient_id, data] --> B[value_kg = float data]
    B --> C{20 <= value <= 400?}
    C -- não --> C1[ValidationError]
    C -- sim --> D[measured_at = data ou now]
    D --> E{não futuro?}
    E -- não --> E1[ValidationError]
    E -- sim --> F[WeightLog.create patient_id]
    F --> G[return id, value_kg, measured_at]
```

> `persist_sleep_log`, `persist_activity_log` e `persist_nutrition_note` seguem o mesmo padrão com regras próprias (sono: 0<h≤24 e quality 1–10 default 5 · atividade: duration_min≥1 e type obrigatório/truncado 40 · nutrição: 10≤len≤1000). Chamadas de `apps.ai_engine/services/user_data_capture.py`.

# Fluxograma — Módulo `ai_engine`

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Pipeline de geração (REST `generate` e SSE `generate_stream`)

> A entrada é sempre a mesma: `(user_id, conversation_id, query, is_first_message)`.
> Diferenças REST vs SSE: o REST retorna `GenerateResult`; o SSE emite eventos `citation` → `token*` → `done` (ou `error`).

```mermaid
flowchart TD
    A[generate / generate_stream] --> B[check_input query]
    B -- bloqueado --> C[resposta canônica + DISCLAIMER]
    C --> D{SSE?}
    D -- sim --> E[yield token + done blocked=True tokens=0]
    D -- não --> F[GenerateResult blocked=True tokens=0]
    B -- liberado --> G[capture_from_message]
    G --> H[_resolve_messages]
    H --> I[provider = get_provider]
    I --> J{REST ou SSE?}

    J -- REST --> K[provider.complete]
    K --> L[check_output]
    L -- bloqueado --> M[canned_reply + DISCLAIMER, blocked=True]
    L -- liberado --> N{termina com DISCLAIMER?}
    N -- não --> O[anexa DISCLAIMER]
    N -- sim --> P[GenerateResult content]
    O --> P

    J -- SSE --> Q[provider.stream]
    Q --> R[acumula tokens e emite evento token]
    R --> S[check_output text]
    S -- bloqueado --> T[yield token supressão + done blocked=True tokens=0]
    S -- liberado --> U[yield done blocked=False tokens=palavras]
    Q -- exceção --> V[yield error LLM_PROVIDER_ERROR]
```

---

## 2. Guardrail de entrada (`check_input`)

```mermaid
flowchart TD
    A[check_input text] --> B{URGENCY_PATTERNS}
    B -- match --> B1[reason=urgency → URGENCY_REPLY]
    B -- não --> C{DIAGNOSIS_PATTERNS}
    C -- match --> C1[reason=diagnosis → DIAGNOSIS_REPLY]
    C -- não --> D{PRESCRIPTION_PATTERNS}
    D -- match --> D1[reason=prescription → PRESCRIPTION_REPLY]
    D -- não --> E{_is_gibberish}
    E -- sim --> E1[reason=gibberish → GIBBERISH_REPLY]
    E -- não --> F[allowed=True]
    B1 --> Z[allowed=False]
    C1 --> Z
    D1 --> Z
    E1 --> Z
```

---

## 3. Onboarding — seleção de prompt (`_resolve_messages`)

```mermaid
flowchart TD
    A[_resolve_messages] --> B[get_user_readiness patient_id]
    B -- is_complete --> C[modo normal: RAG + health_summary + prompts.py]
    B -- incompleto --> D{is_first_message?}
    D -- sim --> E[modo focus: ONBOARDING_FOCUS_TEMPLATE]
    D -- não --> F[modo soft: prompt normal + ONBOARDING_SOFT_APPENDIX]
    E --> G[onboarding_mode=focus, sem citações]
    F --> H[onboarding_mode=soft]
    C --> I[citações do RAG]
```

---

## 4. Captura automática de dados do paciente (`capture_from_message`)

```mermaid
flowchart TD
    A[capture_from_message] --> B{message_likely_has_health_data?}
    B -- não --> B1[patient_id da conversa + still_missing]
    B -- sim --> C[parse_rules → ExtractedUserData]
    C --> D{_should_call_llm?}
    D -- sim --> E[extract_with_llm]
    E --> F[merge_extracted: regras vencem, LLM preenche gaps]
    D -- não --> F
    F --> G{has_actionable_data?}
    G -- não --> G1[patient_id + still_missing]
    G -- sim --> H[_ensure_patient: cria/resolve Patient por nome e DOB]
    H --> I[_persist_health_data: profile, weight, sleep, activity, nutrition]
    I --> J[get_user_readiness → still_missing]
    J --> K[CaptureResult]
```

---

## 5. Providers — fábrica e coalescing do Gemini

```mermaid
flowchart LR
    A[get_provider] --> B{LLM_PROVIDER}
    B -- openai --> C[OpenAIProvider]
    B -- gemini --> D[GeminiProvider]
    D --> E[complete/stream: _build separa system e coalesce roles iguais]
    B -- outro --> F[RuntimeError LLM_PROVIDER desconhecido]
    C --> G[complete/stream: openai.chat.completions]
```

# User Stories — Recomendações de IA

> Fluxo: geração, guardrails, onboarding por prontidão e captura automática de dados.
> Cobertura: módulo `ai_engine`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-IA-01 — Gerar resposta educativa

**Como** médico,
**quero** receber apoio clínico educativo (hipóteses, condutas, evidências),
**para** fundamentar minhas decisões sem que a IA substitua meu julgamento.

- Critérios de aceite:
  - `generate` (REST) → `GenerateResult {content, tokens_used, blocked_by_guardrail, citations, onboarding_mode, missing_basics, data_capture}`.
  - `generate_stream` (SSE) → eventos citation/token/done.
  - Resposta com contexto RAG (`search`, top-5, score ≥ 0.75) e health summary. 🟢

## US-IA-02 — Guardrail clínico

**Como** plataforma,
**quero** bloquear pedidos de urgência, diagnóstico e prescrição (e texto sem sentido),
**para** nunca emitir diagnóstico ou prescrição (restrição crítica).

- Critérios de aceite:
  - `check_input`: ordem fixa urgency → diagnosis → prescription → gibberish; primeiro match bloqueia.
  - `check_output`: `FORBIDDEN_OUTPUT_PATTERNS` bloqueiam saída.
  - Bloqueio → resposta canônica + DISCLAIMER, `tokens_used=0`, `blocked=True`. 🟢

## US-IA-03 — Onboarding por prontidão do perfil

**Como** novo usuário com perfil incompleto,
**quero** que a IA me ajude a completar os dados do paciente,
**para** acelerar o cadastro sem fricção.

- Critérios de aceite:
  - Perfil completo → prompt normal (RAG + resumo).
  - Incompleto + 1ª mensagem → modo `focus` (template de onboarding, sem citações).
  - Incompleto + demais → modo `soft` (prompt normal + apêndice). 🟢

## US-IA-04 — Captura automática de dados

**Como** médico,
**quero** que peso, sono, atividade e refeições mencionados no chat sejam salvos automaticamente,
**para** não precisar digitar esses dados duas vezes.

- Critérios de aceite:
  - `capture_from_message`: detecção → `parse_rules` (regex) → LLM preenche gaps (`merge_extracted`, rules-win) → `_ensure_patient` → `_persist_health_data`.
  - Mensagem sem dados → nada persistido, `still_missing` atualizado.
  - Erros viram `CaptureResult.errors`, sem quebrar o turno. 🟢

## US-IA-05 — Providers configuráveis

**Como** equipe de plataforma,
**quero** alternar o provider LLM por env (`LLM_PROVIDER=openai|gemini`),
**para** escolher o melhor custo/qualidade.

- Critérios de aceite:
  - `get_provider()` → OpenAIProvider ou GeminiProvider (mesmo `Protocol`).
  - Gemini: `_build` separa system e coalesce roles iguais (SDK exige alternância).
  - Provider desconhecido → `RuntimeError`. 🟢 (🔴 `anthropic` documentado mas não implementado)

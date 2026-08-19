# AI Engine / Generate, Tarefas de Implementação

> Sequência executável para reimplementar a geração a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Guardrails `check_input` / `check_output` (ver guardrail)
- [ ] Captura automática `capture_from_message` (ver capture)
- [ ] Seleção de prompt `_resolve_messages` (ver onboarding)
- [ ] Factory `get_provider` (ver providers)

## Tarefas

- [ ] **T-01**, `generate` (REST) com guardrail de entrada/saída, captura e DISCLAIMER
  - Origem no legado: `apps/ai_engine/orchestrator.py:183-258`
  - Critério de pronto: bloquear entrada/saída → canned reply + DISCLAIMER, `tokens=0`, `blocked=True`; liberado → anexa DISCLAIMER se ausente; `record("MESSAGE_SENT")` com latency
  - Confiança: 🟢

- [ ] **T-02**, `generate_stream` (SSE) com eventos citation/token/done/error
  - Origem no legado: `apps/ai_engine/orchestrator.py:261-348`
  - Critério de pronto: citation antes dos tokens; token por chunk; done com `tokens_used=len(text.split())`; error em exceção
  - Confiança: 🟢

- [ ] **T-03**, Dataclass `GenerateResult` com `content, tokens_used, blocked_by_guardrail, citations, onboarding_mode, missing_basics, data_capture`
  - Origem no legado: `apps/ai_engine/orchestrator.py:31-39`
  - Confiança: 🟢

- [ ] **T-04**, `capture_meta` opcional: só quando `saved`/`errors` não-vazios
  - Origem no legado: `orchestrator.py:203-208`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Happy path REST: content liberado com DISCLAIMER anexado quando ausente
- [ ] **TT-02**, Guardrail de entrada bloqueia → `tokens=0, blocked=True`
- [ ] **TT-03**, Guardrail de saída bloqueia → canned reply + DISCLAIMER
- [ ] **TT-04**, SSE: sequência citation → tokens → done com `blocked=False`
- [ ] **TT-05**, SSE: exceção no stream → evento error `LLM_PROVIDER_ERROR`
- [ ] **TT-06**, Nenhum log contém conteúdo da mensagem ou PII

## Ordem Sugerida

1. T-03 (contrato) → T-01 → T-02 → T-04.
2. Testes TT-01 a TT-06 (mockar LLM externo).

## Lacunas Pendentes (🔴)

- [ ] Corrigir `patient_created` no streaming (atributo inexistente em `CaptureResult`).
- [ ] Decidir `tokens_used` real no streaming (hoje conta palavras).
- [ ] Anexar `DISCLAIMER` programaticamente no streaming (conformidade LGPD).
- [ ] Substituir catch-all do stream por tratamento específico (não mascarar bugs como `LLM_PROVIDER_ERROR`).

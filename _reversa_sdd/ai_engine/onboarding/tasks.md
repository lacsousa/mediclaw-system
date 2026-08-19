# AI Engine / Onboarding, Tarefas de Implementação

> Sequência executável para reimplementar o onboarding a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] `get_user_readiness` (skills/user_readiness)
- [ ] Templates de onboarding em `prompts.py` (focus, soft, still-missing, capture-saved)
- [ ] `health_summary` e `search` (RAG)

## Tarefas

- [ ] **T-01**, `_resolve_messages` com os três modos (normal/focus/soft)
  - Origem no legado: `apps/ai_engine/orchestrator.py:158-180`
  - Critério de pronto: completo → normal; incompleto+1ª → focus sem citações; incompleto+demais → soft
  - Confiança: 🟢

- [ ] **T-02**, `_build_messages` com RAG + health summary + apêndices
  - Origem no legado: `apps/ai_engine/orchestrator.py:115-155`
  - Critério de pronto: system prompt formata `SYSTEM_PROMPT_TEMPLATE`; fallback RAG; `_append_capture_context`
  - Confiança: 🟢

- [ ] **T-03**, `_build_onboarding_focus_messages` com `onboarding_mode="focus"`
  - Origem no legado: `apps/ai_engine/orchestrator.py:171-176`
  - Critério de pronto: usa `ONBOARDING_FOCUS_TEMPLATE` e `citations=[]`
  - Confiança: 🟢

- [ ] **T-04**, Histórico `_history_with_query` com janela e deduplicação do turno
  - Origem no legado: `apps/ai_engine/orchestrator.py:78-97`
  - Critério de pronto: últimos `HISTORY_WINDOW` (6), remove user com `content == query`, anexa o turno final
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Perfil completo → modo normal com citações e health summary no prompt
- [ ] **TT-02**, Incompleto + 1ª mensagem → `onboarding_mode=focus`, sem citações
- [ ] **TT-03**, Incompleto + não-primeira → `onboarding_mode=soft` com apêndice
- [ ] **TT-04**, RAG sem chunks → fallback no contexto
- [ ] **TT-05**, Turno USER duplicado é deduplicado no histórico

## Ordem Sugerida

1. T-04 → T-02 → T-03 → T-01.
2. Testes TT-01 a TT-05 (mockar `search` e LLM).

## Lacunas Pendentes (🔴)

- [ ] Confirmar comportamento com `patient_id=None` (perfil tratado como incompleto).

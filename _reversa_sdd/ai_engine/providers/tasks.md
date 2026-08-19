# AI Engine / Providers, Tarefas de Implementação

> Sequência executável para reimplementar os providers a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Deps OpenAI SDK e Google GenAI SDK
- [ ] Env `LLM_PROVIDER`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `CHAT_MODEL`

## Tarefas

- [ ] **T-01**, `ChatMessage` (TypedDict) e Protocol `LLMProvider` com `stream`/`complete`/`complete_json`
  - Origem no legado: `apps/ai_engine/providers/base.py:4-14`
  - Confiança: 🟢

- [ ] **T-02**, `get_provider` factory por env `LLM_PROVIDER` com `RuntimeError` para desconhecido
  - Origem no legado: `apps/ai_engine/providers/__init__.py:4-14`
  - Critério de pronto: `openai` → OpenAIProvider; `gemini` → GeminiProvider; outro → `RuntimeError`
  - Confiança: 🟢

- [ ] **T-03**, `OpenAIProvider` com `complete`/`stream` e tokens do `usage`
  - Origem no legado: `apps/ai_engine/providers/openai_provider.py`
  - Critério de pronto: model `CHAT_MODEL`; exceções do SDK → própria
  - Confiança: 🟢

- [ ] **T-04**, `GeminiProvider` com `_build` (system separado + coalescing de roles iguais)
  - Origem no legado: `apps/ai_engine/providers/gemini_provider.py:17-34`
  - Critério de pronto: roles alternados; system como `system_instruction`; exceções do SDK → própria
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Factory: openai → OpenAIProvider, gemini → GeminiProvider
- [ ] **TT-02**, Factory: provider desconhecido → `RuntimeError`
- [ ] **TT-03**, `complete`/`stream` retornam conteúdo e contagem de tokens (mock SDK)
- [ ] **TT-04**, Gemini `_build`: system extraído; system+system consecutivos concatenados
- [ ] **TT-05**, Gemini `_build`: roles alternados preservados
- [ ] **TT-06**, Erro do SDK vira exceção própria

## Ordem Sugerida

1. T-01 → T-02 → T-03 → T-04.
2. Testes TT-01 a TT-06 (mockar SDKs).

## Lacunas Pendentes (🔴)

- [ ] Implementar provider Anthropic (documentado, ausente no código) ou remover da documentação.
- [ ] Revisar variáveis de env documentadas (`GOOGLE_API_KEY` vs `ANTHROPIC_API_KEY` no `.env.example`).

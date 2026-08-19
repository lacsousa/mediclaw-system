# AI Engine / Providers, Design Técnico

> Contrato operacional de **COMO** os providers são construídos, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `get_provider` | `() -> LLMProvider` | `OpenAIProvider`/`GeminiProvider` (`providers/__init__.py:4-14`) |
| `LLMProvider` | Protocol: `stream(messages, max_tokens)`, `complete(messages, max_tokens)` — **`complete_json` fora do Protocol** (só nas implementações concretas) | `providers/base.py:9-14` |
| `ChatMessage` | TypedDict `{role: system\|user\|assistant, content: str}` | `providers/base.py:4-6` |

## Fluxo Principal

1. `get_provider()` lê env `LLM_PROVIDER`. (`providers/__init__.py:4-14`) 🟢
2. **`openai`** → `OpenAIProvider`:
   - `OpenAI(api_key=OPENAI_API_KEY)`, model `CHAT_MODEL` (default `gpt-4o-mini`). (`openai_provider.py:13-14`) 🟢
   - `complete` → `openai.chat.completions`; `tokens_used` = `usage.total_tokens`. (`openai_provider.py:38`) 🟢
   - `stream` → iterator de chunks de conteúdo. 🟢
   - Exceções do SDK → exceção própria. (`openai_provider.py:29,40`) 🟢
3. **`gemini`** → `GeminiProvider`:
   - `genai.Client(api_key=GOOGLE_API_KEY)`, model default `gemini-2.0-flash`. (`gemini_provider.py:14-15`) 🟢
   - `_build(messages)` separa `system` e **coalesce roles iguais consecutivos** (Gemini não aceita `system` nem roles repetidos). (`gemini_provider.py:17-34`) 🟢
   - `complete`/`stream` → `genai.generate_content`/`stream`; exceções do SDK → própria. (`gemini_provider.py:53,67`) 🟢
4. **Outro valor** → `RuntimeError("LLM_PROVIDER desconhecido")`. 🟢

### Gemini `_build` — detalhe

1. Extrai mensagem(s) `system` e converte para `system_instruction`. 🟢
2. Percorre `messages`; role consecutivo igual ao anterior → concatena `content` na mesma mensagem (`"{prev}\n{cur}"`). 🟢
3. `assistant`/`user` mantidos; sem `system` inline no corpo. 🟢

## Fluxos Alternativos

- **[`LLM_PROVIDER=anthropic`]:** `RuntimeError` do factory sobe ao chamador (DRF handler / SSE). 🟢 — divergência documentada com o PROJECT-CONTEXT (que lista anthropic como opção).
- **[Erro de rede/SDK]:** exceção própria propagada; no stream vira `LLM_PROVIDER_ERROR`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| OpenAI SDK | Geração OpenAI | `OpenAI(...)`; `openai.chat.completions` |
| Google GenAI SDK | Geração Gemini | `genai.Client(...)`; `generate_content` |
| `config.settings` / env | Config | `LLM_PROVIDER`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `CHAT_MODEL` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Provider via factory com `Protocol` (duck typing) | `providers/__init__.py:4-14`; `base.py:9-14` | 🟢 |
| Gemini coalesce roles iguais e separa system no `_build` | `gemini_provider.py:17-34` | 🟢 |
| `complete_json` para extração estruturada (captura) — **não integra o Protocol**; tipo de provider customizado não garante o método | `providers/base.py`; `data_extraction_llm.py:61-72` | 🟡 [Revisão Codex] |
| Modelos default diferentes por provider (`gpt-4o-mini` vs `gemini-2.0-flash`) | `openai_provider.py:14`; `gemini_provider.py:15` | 🟢 |
| `tokens_used` medido no SDK do provider (OpenAI `usage.total_tokens`) | `openai_provider.py:38` | 🟢 |

## Riscos e Lacunas

- 🟡 **Provider Anthropic documentado mas ausente** — `get_provider` só conhece `openai`/`gemini`; `LLM_PROVIDER=anthropic` quebra com `RuntimeError`. Alinhar docs com código.
- 🟡 Google SDK exige roles alternados; o coalescing no `_build` é o único lugar que garante isso — qualquer caminho que pule o `_build` quebra.
- 🟡 `GOOGLE_API_KEY` não consta no `.env.example` do PROJECT-CONTEXT (que lista `ANTHROPIC_API_KEY`) — revisar variáveis documentadas.

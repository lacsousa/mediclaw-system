# AI Engine / Providers — Requisitos

> Contrato operacional do caso de uso **Factory e implementações de provider LLM** (`get_provider`, OpenAI, Gemini).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Fábrica que seleciona o provider LLM pelo env `LLM_PROVIDER` (`openai` | `gemini`). Ambos implementam o mesmo `Protocol` (`stream`/`complete`/`complete_json`). O Gemini exige roles alternados — mensagens consecutivas do mesmo role são concatenadas no `_build`.

## Regras de Negócio

- **RN-01** — `get_provider()` retorna `OpenAIProvider` se `LLM_PROVIDER=openai`; `GeminiProvider` se `gemini`. 🟢
- **RN-02** — `LLM_PROVIDER` desconhecido → `RuntimeError`. 🟢 (Anthropic documentado em PROJECT-CONTEXT **quebra** aqui.)
- **RN-03** — Protocol `LLMProvider` declara **apenas** `stream(messages, max_tokens)` e `complete(messages, max_tokens)` (`base.py:9-14`). `complete_json` existe nas implementações concretas, mas **não** no contrato estrutural — um provider customizado conformante ao Protocol não é obrigado a implementá-lo. 🟡 [Revisão Codex]
- **RN-04** — Gemini: roles alternados exigidos; `_build` concatena roles iguais consecutivos e separa system. 🟢
- **RN-05** — Erros do SDK viram exceções próprias (`openai_provider.py:29,40`; `gemini_provider.py:53,67`). 🟢
- **RN-06** — `tokens_used`: OpenAI usa `usage.total_tokens`; Gemini usa contagem própria. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Selecionar provider por env | Must | `LLM_PROVIDER=openai` → OpenAIProvider; `=gemini` → GeminiProvider |
| RF-02 | Rejeitar provider desconhecido | Must | Outro valor → `RuntimeError` |
| RF-03 | Completar geração | Must | `complete(messages, max_tokens)` → `(content, tokens)` |
| RF-04 | Streamar geração | Must | `stream(messages, max_tokens)` → iterator de tokens |
| RF-05 | Completar com JSON estruturado | Must | `complete_json(...)` → `ExtractedUserData` parseado (usado na captura) |
| RF-06 | Concatenar roles no Gemini | Must | System separado; roles iguais consecutivos mesclados |

## Critérios de Aceitação

```gherkin
Dado LLM_PROVIDER=openai
Quando chamo get_provider
Então retorna OpenAIProvider

Dado LLM_PROVIDER=anthropic
Quando chamo get_provider
Então lança RuntimeError (provider não suportado no código)

Dada uma lista com dois system seguidos para o Gemini
Quando construo o payload
Então system é extraído e os roles iguais consecutivos são concatenados
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/ai_engine/providers/__init__.py:4-14` | `get_provider` | 🟢 |
| `apps/ai_engine/providers/base.py:4-14` | `ChatMessage`, `LLMProvider` (Protocol) | 🟢 |
| `apps/ai_engine/providers/openai_provider.py:13-14` | `OpenAIProvider` (model `CHAT_MODEL`, default `gpt-4o-mini`) | 🟢 |
| `apps/ai_engine/providers/gemini_provider.py:14-15` | `GeminiProvider` (model default `gemini-2.0-flash`) | 🟢 |
| `apps/ai_engine/providers/gemini_provider.py:17-34` | `_build` (coalescing de roles) | 🟢 |

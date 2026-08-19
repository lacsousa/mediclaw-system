# ADR-003 — Guardrails clínicos: a IA nunca diagnostica nem prescreve

**Status:** Aceito 🟢
**Data:** desde o início do projeto (prompts e guardrails presentes no primeiro commit)
**Fonte:** `ai_engine/guardrails.py`, `ai_engine/prompts.py`, `PROJECT-CONTEXT.md`, testes `tests/ai_engine/test_guardrails.py`.

## Contexto

A plataforma apoia **longevidade e bem-estar preventivo** com IA. Como lida com dados de saúde (sensíveis sob LGPD) e contexto clínico, há risco regulatório e ético de a IA emitir diagnóstico ou prescrição. A premissa de produto é **educativa e preventiva**: o médico é o responsável pela conduta.

## Decisão

- A IA **nunca** emite diagnóstico definitivo ou prescrição; oferece hipóteses diferenciais e condutas em linguagem de apoio ("considerar", "avaliar", "sugerir investigar").
- **Guarda dupla:** `check_input` (entrada) e `check_output` (saída), com regex por categoria:
  - `urgency` (dor torácica, falta de ar, desmaio) — **prioridade máxima** → orienta estabilização e encaminhamento (SAMU 192).
  - `diagnosis` → responde que não pode fechar diagnóstico.
  - `prescription` → responde que prescrição é do médico assistente.
  - `gibberish` → pede reformulação.
  - `forbidden_output` → suprime respostas com padrões proibidos ("você tem câncer", "tome X mg", "diagnóstico é").
- **Disclaimer obrigatório** no fim de toda resposta com viés clínico (anexado pelo orquestrador se ausente).
- O system prompt instrui a usar **apenas** o contexto científico do RAG e a citar fontes — sem evidência, responder genericamente sem inventar fontes.

## Consequências

- Toda resposta bloqueada retorna `canned_reply + DISCLAIMER`, com `blocked_by_guardrail=True` e `tokens_used=0`.
- Bloqueios são auditados como eventos `GUARDRAIL_BLOCKED` (stub no MVP) e o `Message.metadata` registra o modo de onboarding quando aplicável.
- O mecanismo é determinístico (regex), testável e sem custo de LLM para bloqueios de entrada — mas depende de manter o vocabulário de padrões atualizado (regressões possíveis com variações de linguagem).

## Alternativas consideradas

- Confiar apenas no system prompt (sem guardrails) — rejeitado: prompt não é garantia de comportamento.
- Classificador de intenção via LLM — não adotado no MVP por custo/latência; regex é determinístico.

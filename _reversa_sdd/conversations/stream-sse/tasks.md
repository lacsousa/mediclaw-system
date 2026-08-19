# Conversations / Stream SSE, Tarefas de Implementação

> Sequência executável para reimplementar o streaming SSE a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Orquestrador com geração em streaming (`generate_stream` a confirmar)
- [ ] Utilidade de evento SSE (`apps/common/views.py`)

## Tarefas

- [ ] **T-01**, View pura `conversation_stream` com auth via query param
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: `?token=` válido → prossegue; inválido/ausente → 401; conversa fora do escopo → 404
  - Confiança: 🟢

- [ ] **T-02**, Emissão de eventos SSE por chunk
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: `event: message` + `data: {chunk}` por token; `data: {"done": true}` ao final; headers de stream corretos
  - Confiança: 🟡

- [ ] **T-03**, Tratamento de erro do LLM no meio do stream
  - Critério de pronto: emite `LLM_PROVIDER_ERROR` como evento e encerra sem quebrar a conexão
  - Confiança: 🟡

## Tarefas de Teste

- [ ] **TT-01**, Happy path: sequência de chunks terminando em `done: true`
- [ ] **TT-02**, Token ausente → 401
- [ ] **TT-03**, Token inválido → 401
- [ ] **TT-04**, Conversa inexistente/outro dono → 404
- [ ] **TT-05**, Erro do LLM → evento de erro e stream encerrado

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-05 (mockar LLM de streaming).

## Lacunas Pendentes (🔴)

- [ ] Confirmar formato exato dos eventos SSE no código legado.
- [ ] Confirmar nome/assinatura do método de streaming do orquestrador.
- [ ] Verificar se headers anti-buffer (`X-Accel-Buffering`, `Cache-Control`) estão presentes no legado.

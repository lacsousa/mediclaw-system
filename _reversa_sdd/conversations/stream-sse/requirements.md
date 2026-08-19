# Conversations / Stream SSE — Requisitos

> Contrato operacional do caso de uso **Streaming da resposta via SSE** (`GET /api/v1/conversations/<id>/stream/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Revisado em 2026-08-19 após revisão cruzada — corrige símbolos, códigos de erro e wire format. [Revisão Codex]

## Visão Geral

Transmite a resposta do assistente em tempo real via **Server-Sent Events** (SSE). É uma view Django pura (sem DRF) — `stream(request, conv_id)` — que recebe o token JWT via query param `?token=` (EventSource não envia headers de autorização), valida a conversa e o dono, persiste a mensagem USER antes da chamada e streameia os eventos do orquestrador (`token`/`citation`/`done`/`error`) como `data: {json}\n\n`. **Não possui throttle próprio.**

## Regras de Negócio

- **RN-01** — Rota sem DRF: view pura Django, `Content-Type: text/event-stream`. 🟢
- **RN-02** — Auth via query param `?token=<access>`; token ausente **ou** inválido → evento SSE `{"type":"error","code":"UNAUTHORIZED"}` com status 401 (não `MISSING_TOKEN`/`INVALID_TOKEN`). 🟢
- **RN-03** — Conversa inexistente ou de outro dono → evento SSE `NOT_FOUND` com 404. 🟢
- **RN-04** — `prompt` vazio → evento SSE `VALIDATION_ERROR` com 400. 🟢
- **RN-05** — Limite de mensagens atingido (`count >= MAX_MESSAGES`) → evento SSE `CONVERSATION_FULL` com 400. 🟢
- **RN-06** — **Sem throttle**: `@throttle_classes([ChatThrottle])` não é aplicado ao `stream` (apenas a `post_message`) — caminho de maior custo sem limite de requisição. 🟢 (lacuna de custo/segurança, ver architecture.md D4)
- **RN-07** — O `DISCLAIMER` **não** é anexado programaticamente no caminho normal do stream (apenas nos bloqueios de guardrail de entrada) — a conformidade LGPD depende do LLM. 🔴
- **RN-08** — Wire format: cada evento é yield como `data: {json}\n\n`, **sem linha `event:`**; o tipo é discriminado pelo campo `type` do JSON. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Abrir stream SSE | Must | GET `/api/v1/conversations/<id>/stream/?token=<jwt>&prompt=oi` → 200 `text/event-stream` |
| RF-02 | Autenticar via token query param | Must | Token ausente/inválido → evento SSE `UNAUTHORIZED` com 401 |
| RF-03 | Escopar conversa ao dono | Must | Conversa inexistente/de outro dono → evento SSE `NOT_FOUND` com 404 |
| RF-04 | Validar prompt | Must | `prompt` vazio → evento SSE `VALIDATION_ERROR` com 400 |
| RF-05 | Aplicar limite de mensagens | Must | `count >= MAX_MESSAGES` → evento SSE `CONVERSATION_FULL` com 400 |
| RF-06 | Emitir eventos do orquestrador | Must | Eventos `token` (por token), `citation` (por chunk RAG), `done` (fim) ou `error` (`LLM_PROVIDER_ERROR`), todos `data: {json}\n\n` |
| RF-07 | Persistir turno | Must | Mensagem USER persistida antes da chamada; ASSISTANT persistida no evento `done` com `tokens_used`, `blocked_by_guardrail`, metadata (citations/onboarding/capture) |
| RF-08 | Título automático | Should | Se vazio ou `"Nova conversa"`, recebe os primeiros 80 chars do prompt |

## Critérios de Aceitação

```gherkin
Dado um token válido e uma conversa do dono
Quando abro GET /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=oi
Então recebo 200 com text/event-stream e eventos data: {json} (token*, citation*, done)

Dado um token inválido ou ausente
Quando abro GET /api/v1/conversations/<id>/stream/?token=...
Então recebo 401 com data: {"type": "error", "code": "UNAUTHORIZED", ...}

Dado uma conversa inexistente ou de outro dono
Quando abro GET /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=oi
Então recebo 404 com data: {"type": "error", "code": "NOT_FOUND", ...}

Dado prompt vazio com token válido
Quando abro GET /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=
Então recebo 400 com data: {"type": "error", "code": "VALIDATION_ERROR", ...}

Dado uma conversa com 50 mensagens
Quando abro GET /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=oi
Então recebo 400 com data: {"type": "error", "code": "CONVERSATION_FULL", ...}

Dado um provider que lança exceção no meio do stream
Quando abro GET /api/v1/conversations/<id>/stream/?token=<jwt>&prompt=oi
Então recebo data: {"type": "error", "code": "LLM_PROVIDER_ERROR", ...} e o stream encerra
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/conversations/views.py` | `stream(request, conv_id)` (view pura), `_serialize_patient` | 🟢 |
| `apps/conversations/urls.py` | rota `<id>/stream/` | 🟢 |
| `apps/ai_engine/orchestrator.py` | `generate_stream` (eventos `token`/`citation`/`done`/`error`) | 🟢 |
| `rest_framework_simplejwt.tokens.AccessToken` | validação manual do `?token=` | 🟢 |

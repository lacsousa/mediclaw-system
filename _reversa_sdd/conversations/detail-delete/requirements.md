# Conversations / Detail & Delete — Requisitos

> Contrato operacional do caso de uso **Detalhe e exclusão de conversa** (`GET/DELETE /api/v1/conversations/<id>/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Consulta uma conversa do médico com suas mensagens e deleta (soft delete) a conversa. Acesso escopado ao dono; id de outro médico ou inexistente → 404.

## Regras de Negócio

- **RN-01** — Busca com `doctor=request.user`; fora do escopo/inexistente → 404. 🟢
- **RN-02** — GET retorna a conversa + todas as mensagens (`conv.messages.all`). 🟢
- **RN-03** — DELETE é **soft delete**: `deleted_at = now` + `update_fields=["deleted_at"]`; a conversa some de `Conversation.objects` mas permanece em `all_objects`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Consultar conversa com mensagens | Must | GET `/api/v1/conversations/<id>/` → 200 com mensagens |
| RF-02 | Soft-deletar conversa | Must | DELETE `/api/v1/conversations/<id>/` → 204; `deleted_at` preenchido e conversa some da listagem |
| RF-03 | 404 para fora do escopo | Must | GET/DELETE em id de outro médico ou inexistente → 404 |

## Critérios de Aceitação

```gherkin
Dado uma conversa do médico com 2 mensagens
Quando faço GET em /api/v1/conversations/<id>/
Então recebo 200 com a conversa e suas mensagens

Dado uma conversa do médico
Quando faço DELETE em /api/v1/conversations/<id>/
Então recebo 204 e a conversa não aparece mais em GET /conversations/

Dado um id de outro médico ou inexistente
Quando faço GET/DELETE em /api/v1/conversations/<id>/
Então recebo 404 NOT_FOUND
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/conversations/views.py` | `conversation_detail`, `conversation_delete` | 🟢 |
| `apps/conversations/models.py` | `Conversation` (soft delete, `all_objects`) | 🟢 |

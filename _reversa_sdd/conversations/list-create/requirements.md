# Conversations / List & Create — Requisitos

> Contrato operacional do caso de uso **Listar e criar conversas** (`GET/POST /api/v1/conversations/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Lista as conversas do médico autenticado (excluindo soft-deletadas) com paginação manual (20/página), e cria uma nova conversa vazia com título "Nova conversa".

## Regras de Negócio

- **RN-01** — Listagem filtrada por `doctor=request.user` e apenas não-deletadas (`deleted_at__isnull=True`). 🟢
- **RN-02** — Paginação manual: 20/página, `next` com `?page=N+1`. 🟢
- **RN-03** — POST cria conversa com `title="Nova conversa"`, `patient=null`. 🟢
- **RN-04** — Resposta passa pelo `EnvelopeJSONRenderer` → `{data, error, meta}`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Listar conversas do médico com paginação | Must | GET `/api/v1/conversations/` → 200 `{results, count, next}` |
| RF-02 | Criar conversa vazia | Must | POST `/api/v1/conversations/` → 201 `{id, title, patient, timestamps}` |
| RF-03 | Não listar conversas soft-deletadas | Must | Conversa com `deleted_at` preenchido não aparece na lista |

## Critérios de Aceitação

```gherkin
Dado um médico autenticado com 3 conversas
Quando faço GET em /api/v1/conversations/
Então recebo 200 com 3 itens, count e next

Dado um médico autenticado
Quando faço POST em /api/v1/conversations/
Então recebo 201 com id, title "Nova conversa" e patient null

Dado uma conversa soft-deletada
Quando faço GET em /api/v1/conversations/
Então ela não aparece na listagem
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/conversations/views.py` | `list_conversations`, `create_conversation` | 🟢 |
| `apps/conversations/models.py` | `Conversation`, manager (filtro `deleted_at`) | 🟢 |
| `apps/conversations/urls.py` | rotas `/api/v1/conversations/` | 🟢 |

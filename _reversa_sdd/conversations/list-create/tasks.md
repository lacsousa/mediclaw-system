# Conversations / List & Create, Tarefas de Implementação

> Sequência executável para reimplementar listar/criar conversas a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `Conversation` com manager de soft-delete e `doctor`/`patient`

## Tarefas

- [ ] **T-01**, Modelo `Conversation` com manager filtrando `deleted_at__isnull=True`
  - Origem no legado: `apps/conversations/models.py`
  - Critério de pronto: `Conversation.objects` exclui soft-deletadas; `all_objects` inclui; campos `title`, `doctor`, `patient`, `deleted_at`
  - Confiança: 🟢

- [ ] **T-02**, View `list_conversations` com paginação manual
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: filtro `doctor=request.user` + `select_related("patient")`; 20/página; `{results, count, next}`
  - Confiança: 🟢

- [ ] **T-03**, View `create_conversation` com título padrão
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: POST → 201 com `title="Nova conversa"`, `patient=null`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, GET lista conversas do médico com paginação
- [ ] **TT-02**, GET não lista conversas soft-deletadas
- [ ] **TT-03**, POST cria conversa com título padrão e patient null

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-03.

## Lacunas Pendentes (🔴)

- [ ] Confirmar shape do `patient` na listagem (esperado pelo frontend).

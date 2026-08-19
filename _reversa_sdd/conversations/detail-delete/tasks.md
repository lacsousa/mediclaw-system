# Conversations / Detail & Delete, Tarefas de Implementação

> Sequência executável para reimplementar o detalhe/exclusão a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `Conversation` com soft delete (`deleted_at`, `all_objects`)

## Tarefas

- [ ] **T-01**, View `conversation_detail` com escopo do dono
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: GET → 200 conversa + mensagens; fora do escopo → 404
  - Confiança: 🟢

- [ ] **T-02**, View `conversation_delete` com soft delete
  - Origem no legado: `apps/conversations/views.py`
  - Critério de pronto: DELETE → `deleted_at=now` + `update_fields`; 204; some da listagem
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, GET detalhe → 200 com mensagens
- [ ] **TT-02**, DELETE → 204 e conversa some da listagem (mas permanece em `all_objects`)
- [ ] **TT-03**, GET/DELETE em id de outro médico ou inexistente → 404

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 a TT-03.

## Lacunas Pendentes (🔴)

- [ ] Definir política de retenção/expurgo de mensagens soft-deletadas (LGPD 90 dias).

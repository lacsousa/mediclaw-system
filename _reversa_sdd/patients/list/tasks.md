# Patients / List, Tarefas de Implementação

> Sequência executável para reimplementar a listagem a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `Patient` e modelos de log de saúde existentes
- [ ] Modelo `Conversation` com `deleted_at` e `doctor`

## Tarefas

- [ ] **T-01**, Queryset anotado `_annotate_patients` (count, last_seen, latest_weight)
  - Origem no legado: `apps/patients/views.py:18-33`
  - Critério de pronto: `conversation_count`/`last_seen_at` consideram apenas `deleted_at__isnull=True`; `latest_weight_kg` via subquery top-1 por `measured_at`
  - Confiança: 🟢

- [ ] **T-02**, View `list_patients` com paginação manual
  - Origem no legado: `apps/patients/views.py:36-46`
  - Critério de pronto: filtro `doctor=request.user`; 20/página; `next` correto; `{results, count, next}`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Listagem happy path → 200 com anotações preenchidas
- [ ] **TT-02**, Paginação: 45 pacientes → página 3 com 5 itens, `count=45`, `next=null`
- [ ] **TT-03**, Isolamento: médico só vê os próprios pacientes

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 a TT-03.

## Lacunas Pendentes (🔴)

- [ ] Padronizar paginação (manual vs `DefaultPagination`) com o Architect.

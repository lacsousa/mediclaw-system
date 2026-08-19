# Accounts / persist_user_name, Tarefas de Implementação

> Sequência executável para reimplementar a captura de nome a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `User` com campo `first_name`

## Tarefas

- [ ] **T-01**, Service `persist_user_name` com validação de tamanho e escrita mínima
  - Origem no legado: `apps/accounts/services/persist.py:9-18`
  - Critério de pronto: `strip`; `2 ≤ len ≤ 120` senão `ValidationError`; grava `first_name` com `update_fields`; retorna `{"first_name": cleaned}`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Nome válido → `{"first_name": nome}` persistido
- [ ] **TT-02**, Nome com 1 char ou > 120 → `ValidationError`
- [ ] **TT-03**, Nome com espaços → `strip` aplicado antes de persistir

## Ordem Sugerida

1. T-01, testes TT-01 a TT-03.

## Lacunas Pendentes (🔴)

- [ ] Mapear `User.DoesNotExist` para `NOT_FOUND` no handler global (verificar cobertura do legado).

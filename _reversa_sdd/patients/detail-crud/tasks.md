# Patients / Detail & CRUD, Tarefas de Implementação

> Sequência executável para reimplementar o detalhe/edição/exclusão a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `Patient` e modelos de log de saúde
- [ ] Modelo `Conversation` com FK `patient SET_NULL`

## Tarefas

- [ ] **T-01**, View `patient_detail` com escopo do dono e 404 uniforme
  - Origem no legado: `apps/patients/views.py:50-110`
  - Critério de pronto: GET → `PatientDetailSerializer` com histórico; PATCH parcial; DELETE → 204; fora do escopo/inexistente → 404
  - Confiança: 🟢

- [ ] **T-02**, `PatientDetailSerializer` com sub-serializers de logs e conversas
  - Origem no legado: `apps/patients/serializers.py`
  - Critério de pronto: inclui weight/sleep/activity/nutrition/conversations não-deletadas ordenadas por `-updated_at`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, GET detalhe → 200 com histórico completo
- [ ] **TT-02**, PATCH parcial → apenas o campo enviado alterado
- [ ] **TT-03**, DELETE → 204 e conversa mantém `patient_id` nulo
- [ ] **TT-04**, GET/PATCH/DELETE em id de outro médico ou inexistente → 404 `NOT_FOUND`

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 a TT-04.

## Lacunas Pendentes (🔴)

- [ ] Avaliar carregamento do histórico completo no detalhe (possível paginação futura).

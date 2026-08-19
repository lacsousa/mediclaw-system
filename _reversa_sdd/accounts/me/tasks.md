# Accounts / Me, Tarefas de Implementação

> Sequência executável para reimplementar o perfil próprio a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Autenticação JWT ativa (config `REST_FRAMEWORK` + simplejwt)
- [ ] Modelo `User` e dependentes com `on_delete=CASCADE`

## Tarefas

- [ ] **T-01**, View `me` (GET/PATCH/DELETE) com permissão `IsAuthenticated`
  - Origem no legado: `apps/accounts/views.py:66-93`
  - Critério de pronto: GET → 200 `UserSerializer`; PATCH parcial com `update_fields`; DELETE → 204 em cascata
  - Confiança: 🟢

- [ ] **T-02**, `MeUpdateSerializer` com validação de e-mail único excluindo o próprio `pk`
  - Origem no legado: `apps/accounts/serializers.py:54-61`
  - Critério de pronto: PATCH `{name}` altera apenas `first_name`; `{email}` de outro usuário → 400
  - Confiança: 🟢

- [ ] **T-03**, Rota `GET/PATCH/DELETE /api/v1/auth/me/`
  - Origem no legado: `apps/accounts/urls.py`
  - Critério de pronto: rota montada sob `api/v1/auth/`, protegida por `IsAuthenticated`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, GET `/me` → 200 com `{id, email, first_name, role, accepted_terms_at}`
- [ ] **TT-02**, PATCH `/me` `{name}` → 200 e apenas `first_name` muda (verificar `update_fields`)
- [ ] **TT-03**, PATCH `/me` com e-mail de outro usuário → 400 `VALIDATION_ERROR`
- [ ] **TT-04**, DELETE `/me` → 204 e dados dependentes (pacientes, conversas, logs) removidos em cascata

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-04; TT-04 depende de patients/conversations existirem (cascata).

## Lacunas Pendentes (🔴)

- [ ] Validar com produto se a troca de e-mail no PATCH deve reexigir confirmação/consentimento.

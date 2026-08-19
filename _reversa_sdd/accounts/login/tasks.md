# Accounts / Login, Tarefas de Implementação

> Sequência executável para reimplementar o login a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `User` com `USERNAME_FIELD="email"` e `authenticate` funcionando
- [ ] Pacote `djangorestframework-simplejwt` configurado

## Tarefas

- [ ] **T-01**, View `login` com normalização de e-mail e anti-enumeração
  - Origem no legado: `apps/accounts/views.py:37-53`
  - Critério de pronto: e-mail em minúsculas; inexistente/senha errada/inativo → mesmo 401 `INVALID_CREDENTIALS`; sucesso → 200 `{access, refresh, user}` + `record("LOGIN")`
  - Confiança: 🟢

- [ ] **T-02**, Rota `POST /api/v1/auth/login/` com `AllowAny`
  - Origem no legado: `apps/accounts/urls.py`
  - Critério de pronto: rota montada sob `api/v1/auth/`, sem exigir autenticação
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Login com credenciais corretas → 200 com `{access, refresh, user}`
- [ ] **TT-02**, Login com usuário inexistente, senha errada e usuário inativo → 401 `INVALID_CREDENTIALS` com corpo idêntico nos três casos

## Ordem Sugerida

1. T-01 → T-02.
2. Testes TT-01 e TT-02; TT-02 valida a anti-enumeração (comparar corpos byte a byte).

## Lacunas Pendentes (🔴)

- [ ] Persistência real do evento `LOGIN` (audit stub no legado).

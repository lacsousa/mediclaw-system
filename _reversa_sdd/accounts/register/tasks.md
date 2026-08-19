# Accounts / Register, Tarefas de Implementação

> Sequência executável para reimplementar o cadastro a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `User` e `UserManager` implementados (ver `accounts/tasks.md` T-01/T-02)
- [ ] Pacote `djangorestframework-simplejwt` configurado
- [ ] `ensure_welcome_conversation` disponível (conversations) ou stub no início

## Tarefas

- [ ] **T-01**, `RegisterSerializer` com validações de senha, e-mail único e `accept_terms`
  - Origem no legado: `apps/accounts/serializers.py:6-42`
  - Critério de pronto: rejeita senha fraca, e-mail duplicado (`email__iexact`) e `accept_terms` falso; `create` grava `accepted_terms_at=timezone.now()` e chama `create_user`
  - Confiança: 🟢

- [ ] **T-02**, View `register` emitindo access + refresh e disparando onboarding
  - Origem no legado: `apps/accounts/views.py:19-34`
  - Critério de pronto: POST → 201 `{access, refresh, user}`; chama `record("USER_REGISTERED")` e `ensure_welcome_conversation`
  - Confiança: 🟢

- [ ] **T-03**, Rota `POST /api/v1/auth/register/` com `AllowAny`
  - Origem no legado: `apps/accounts/urls.py`
  - Critério de pronto: rota montada sob `api/v1/auth/`, sem exigir autenticação
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Cadastro happy path → 201 com `{access, refresh, user}`, `accepted_terms_at` preenchido, conversa de boas-vindas criada
- [ ] **TT-02**, Cadastro com senha fraca → 400 `VALIDATION_ERROR`
- [ ] **TT-03**, Cadastro com `accept_terms` ausente → 400 `VALIDATION_ERROR`
- [ ] **TT-04**, Cadastro com e-mail duplicado (diferentes caixas) → 400 `VALIDATION_ERROR`

## Ordem Sugerida

1. T-01 → T-02 → T-03 (serializer → view → rota).
2. Testes TT-01 a TT-04 após a rota pronta; TT-01 depende de `ensure_welcome_conversation`.

## Lacunas Pendentes (🔴)

- [ ] Persistência real do evento `USER_REGISTERED` (audit stub no legado).
- [ ] Throttling específico para cadastro (avaliar se o global anon 30/min é suficiente).

# Accounts, Tarefas de Implementação

> Sequência executável para reimplementar a unit `accounts` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] `AUTH_USER_MODEL` aponta para `accounts.User` no `settings.py` (configurar no início — modelo custom de usuário)
- [ ] Pacote `djangorestframework-simplejwt` instalado e `SIMPLE_JWT` configurado
- [ ] Schema PostgreSQL criado e migrations aplicadas
- [ ] Variáveis `ACCESS_TOKEN_MINUTES` e `REFRESH_TOKEN_DAYS` documentadas no `.env`

## Tarefas

- [ ] **T-01**, Modelo `User` customizado com e-mail como identificador
  - Origem no legado: `apps/accounts/models.py:22-32`
  - Critério de pronto: migration cria tabela com `email` único, `role` default `USER`, `accepted_terms_at` nullable, `username` em branco; `USERNAME_FIELD="email"`
  - Confiança: 🟢

- [ ] **T-02**, `UserManager` com `create_user` e `create_superuser`
  - Origem no legado: `apps/accounts/models.py:5-19`
  - Critério de pronto: `create_user` normaliza e-mail, aplica `set_password`, lança `ValueError` sem e-mail; `create_superuser` força `is_staff`, `is_superuser`, `role=ADMIN`
  - Confiança: 🟢

- [ ] **T-03**, Serializer de cadastro com validação de senha, e-mail único e termos LGPD
  - Origem no legado: `apps/accounts/serializers.py:6-42`
  - Critério de pronto: `PASSWORD_RX` (≥ 8 chars, letra + dígito) rejeita senha fraca; e-mail duplicado via `email__iexact` → erro; `accept_terms` falso → erro; `create` grava `accepted_terms_at=timezone.now()`
  - Confiança: 🟢

- [ ] **T-04**, Endpoint `register` emitindo access + refresh e auditando evento
  - Origem no legado: `apps/accounts/views.py:19-34`
  - Critério de pronto: POST `/api/v1/auth/register/` → 201 `{access, refresh, user}`; chama `ensure_welcome_conversation` e `record("USER_REGISTERED", ...)`
  - Confiança: 🟢

- [ ] **T-05**, Endpoint `login` com anti-enumeração
  - Origem no legado: `apps/accounts/views.py:37-53`
  - Critério de pronto: e-mail normalizado minúsculo; usuário inexistente, senha errada ou inativo → mesmo 401 `INVALID_CREDENTIALS`; sucesso → 200 `{access, refresh, user}`
  - Confiança: 🟢

- [ ] **T-06**, Rota de refresh do token
  - Origem no legado: `apps/accounts/urls.py:3,7`
  - Critério de pronto: `TokenRefreshView` montado em `/api/v1/auth/refresh/`; refresh válido → novo access; inválido → 401
  - Confiança: 🟢

- [ ] **T-07**, Perfil próprio GET/PATCH/DELETE
  - Origem no legado: `apps/accounts/views.py:66-93`
  - Critério de pronto: GET → `UserSerializer`; PATCH parcial via `update_fields` (apenas `name` e/ou `email`, e-mail duplicado exceto próprio → erro); DELETE → 204 com remoção em cascata
  - Confiança: 🟢

- [ ] **T-08**, Serializer de criação de usuário por admin com role definida
  - Origem no legado: `apps/accounts/serializers.py:63-91`
  - Critério de pronto: valida senha, e-mail único e `role ∈ {USER, ADMIN}`; `create` dispara conversa de boas-vindas
  - Confiança: 🟢

- [ ] **T-09**, Endpoint admin + permission custom `IsAdminRole`
  - Origem no legado: `apps/accounts/views.py:56-63`; `apps/common/permissions.py:4-10`
  - Critério de pronto: POST `/api/v1/admin/users/` exige `role == "ADMIN"`; sem role → 403 `FORBIDDEN`; sucesso → 201 `UserSerializer`
  - Confiança: 🟢

- [ ] **T-10**, Service `persist_user_name` para captura via chat
  - Origem no legado: `apps/accounts/services/persist.py:9-18`
  - Critério de pronto: `strip` no nome; `2 ≤ len ≤ 120` senão `ValidationError`; grava `first_name` com `update_fields`; retorna `{"first_name": cleaned}`
  - Confiança: 🟢

- [ ] **T-11**, Integração da conversa de boas-vindas pós-cadastro
  - Origem no legado: `apps/conversations/services/welcome.py:23-50`
  - Critério de pronto: usuário não-ADMIN ganha conversa "Bem-vindo" idempotente com mensagem estática + disclaimer; ADMIN não ganha
  - Confiança: 🟢

- [ ] **T-12**, Montagem das rotas e settings de autenticação
  - Origem no legado: `config/urls.py:31,36`; `apps/accounts/urls.py`; `config/settings.py:131-140`
  - Critério de pronto: `api/v1/auth/` e `api/v1/admin/` montados; `SIMPLE_JWT` com `AUTH_HEADER_TYPES=("Bearer",)` e lifetimes via env
  - Confiança: 🟢

- [ ] **T-13**, Envelope de erro padrão para os códigos da unit
  - Origem no legado: `apps/common/exceptions.py:31-44`; `views.py:44`
  - Critério de pronto: erros de validação e `AppError` retornam `{data: null, error: {code, message, details}, meta: {}}`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Cadastro happy path → 201 com `{access, refresh, user}`, `accepted_terms_at` preenchido, conversa de boas-vindas criada
- [ ] **TT-02**, Cadastro: senha fraca, `accept_terms` ausente e e-mail duplicado → 400 `VALIDATION_ERROR`
- [ ] **TT-03**, Login: credenciais corretas → 200; usuário inexistente, senha errada e inativo → 401 `INVALID_CREDENTIALS` idêntico
- [ ] **TT-04**, PATCH `/me`: atualiza apenas `name` → apenas `first_name` muda; e-mail duplicado (outro usuário) → 400
- [ ] **TT-05**, DELETE `/me`: 204 e dados dependentes (conversas, mensagens, logs) removidos em cascata
- [ ] **TT-06**, POST `/admin/users/`: com role USER → 403 `FORBIDDEN`; com role ADMIN → 201
- [ ] **TT-07**, `persist_user_name`: nome com 1 char → `ValidationError`; nome válido → `{"first_name": nome}`
- [ ] **TT-08**, Refresh: token válido → novo access; token expirado/inválido → 401

## Tarefas de Migração de Dados (se aplicável)

- n/a — reimplementação do schema a partir do zero; nenhum dado legado a migrar. Caso haja base existente com `AUTH_USER_MODEL` anterior, planejar migração do usuário em separado. 🟡

## Ordem Sugerida

1. T-01 → T-02 (modelo + manager) e T-12 (settings/routes) primeiro: base da unit.
2. T-03 → T-04 (cadastro) e T-05 → T-06 (login/refresh): caminho crítico de autenticação.
3. T-07 (perfil) e T-08 → T-09 (admin).
4. T-10 (persist_user_name) e T-11 (welcome) por último: dependem do restante.
5. Testes TT-01 a TT-08 após cada bloco concluído; TT-05 depende de pacientes/conversations existirem (cascata).

## Lacunas Pendentes (🔴)

- [ ] Persistência real de auditoria (`record()` é stub no legado — decidir se a reimplementação persiste ActivityLog no Epic 3 ou já implementa). Origem: `apps/audit/services/log.py`
- [ ] Backend de autenticação: confirmar `AUTHENTICATION_BACKENDS` e `AUTH_USER_MODEL` no settings (não confirmado nesta leitura).
- [ ] Throttling nas rotas `register`/`login`: o checklist de segurança do projeto prevê anon+user, mas não há evidência de implementação no legado.

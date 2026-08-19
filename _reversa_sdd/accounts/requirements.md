# Accounts — Requisitos

> Contrato operacional da unit `accounts` (usuários, perfis e autenticação JWT).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Módulo de identidade do MediClaw: usuário customizado identificado por e-mail, autenticação via JWT (access + refresh) com `djangorestframework-simplejwt`, cadastro com consentimento LGPD explícito, endpoints de perfil (`/me`), criação de usuário por administrador e gravação de nome via captura no chat. Remove dados sensíveis em cascata ao deletar a conta (LGPD Art. 11).

## Responsabilidades

- Autenticar usuários e emitir tokens JWT (access/refresh) no cadastro e login
- Persistir o consentimento LGPD (`accepted_terms_at`) no cadastro
- Expor perfil próprio via `GET/PATCH/DELETE /auth/me/`
- Permitir a médicos criarem pacientes e a admins criarem usuários com role definida
- Garantir unicidade de e-mail (case-insensitive) e normalização para minúsculas
- Disparar a criação da conversa de boas-vindas após cadastro (usuários não-admin)
- Suportar a captura de nome via chat (`persist_user_name`)

## Regras de Negório

- **RN-01** — Senha ≥ 8 caracteres com pelo menos uma letra e um dígito (`PASSWORD_RX`). 🟢
- **RN-02** — E-mail único e case-insensitive (`iexact`), normalizado para minúsculas no cadastro e login. 🟢
- **RN-03** — Falha de credencial e usuário inativo retornam **o mesmo** erro `INVALID_CREDENTIALS` 401 (não vaza qual campo está errado). 🟢
- **RN-04** — Consentimento LGPD: `accept_terms` obrigatório; `accepted_terms_at` gravado no cadastro. 🟢
- **RN-05** — `Me PATCH` atualiza apenas os campos enviados via `update_fields`; mudança de e-mail valida unicidade exceto o próprio usuário. 🟢
- **RN-06** — Deletar a conta remove dados sensíveis em cascata (pacientes, logs biométricos, mensagens) via `on_delete=CASCADE`. 🟢
- **RN-07** — Conversa de boas-vindas criada após cadastro, idempotente, pulada para role `ADMIN`. 🟢
- **RN-08** — `persist_user_name` valida nome com 2 ≤ len ≤ 120 após `trim`; falha lança `ValidationError`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Cadastro de usuário com e-mail, senha e consentimento LGPD, retornando access + refresh + user | Must | POST `/api/v1/auth/register/` com payload válido → 201 com `{access, refresh, user}` e `accepted_terms_at` preenchido |
| RF-02 | Login com e-mail e senha retornando access + refresh + user | Must | POST `/api/v1/auth/login/` com credenciais corretas → 200; incorretas ou usuário inativo → 401 `INVALID_CREDENTIALS` |
| RF-03 | Consultar perfil próprio autenticado | Must | GET `/api/v1/auth/me/` com `Authorization: Bearer <access>` → 200 `UserSerializer` |
| RF-04 | Atualizar perfil próprio (nome e/ou e-mail) | Must | PATCH `/api/v1/auth/me/` atualizando apenas campos enviados → 200 com campos atualizados; e-mail duplicado → 400 `VALIDATION_ERROR` |
| RF-05 | Deletar a própria conta com remoção em cascata | Must | DELETE `/api/v1/auth/me/` → 204; dados do usuário e dependentes removidos do banco |
| RF-06 | Criar usuário com role definida (rota admin) | Should | POST `/api/v1/admin/users/` autenticado com role ADMIN → 201 `UserSerializer`; sem role ADMIN → 403 `FORBIDDEN` |
| RF-07 | Suportar criação de usuário de serviço via `persist_user_name` (captura de nome no chat) | Should | Chamada de service com `user_id` e `name` válidos → `first_name` persistido e retornado |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | Hash de senha via Django `set_password` (nunca armazena senha em texto puro) | `apps/accounts/models.py` (UserManager.create_user) | 🟢 |
| Segurança | Rotas exigem autenticação JWT Bearer; refresh token com `RefreshToken.for_user` | `apps/accounts/views.py`; `config/settings.py` (SIMPLE_JWT) | 🟢 |
| Segurança | Resposta de falha de login não distingue usuário inexistente de senha errada (anti-enumeração) | `apps/accounts/views.py:43` | 🟢 |
| Conformidade | Consentimento LGPD persistido no cadastro (`accepted_terms_at`) | `apps/accounts/serializers.py:22,37` | 🟢 |
| Conformidade | Remoção em cascata de dados sensíveis ao deletar conta | `apps/accounts/views.py:92`; `apps/patients/models.py:11` | 🟢 |

## Critérios de Aceitação

```gherkin
# Cadastro — fluxo feliz
Dado um e-mail válido, senha com ≥ 8 chars (letra + dígito) e accept_terms=true
Quando faço POST em /api/v1/auth/register/
Então recebo 201 com access, refresh e user (accepted_terms_at preenchido)
E uma conversa de boas-vindas é criada para o usuário

# Cadastro — falha de validação
Dado uma senha sem dígito ou accept_terms ausente
Quando faço POST em /api/v1/auth/register/
Então recebo 400 VALIDATION_ERROR com detalhes do campo inválido

# Cadastro — e-mail duplicado
Dado um e-mail já cadastrado (em qualquer caixa)
Quando faço POST em /api/v1/auth/register/ com o mesmo e-mail
Então recebo 400 VALIDATION_ERROR indicando e-mail já em uso

# Login — credenciais inválidas
Dado um e-mail/senha incorretos ou usuário inativo
Quando faço POST em /api/v1/auth/login/
Então recebo 401 INVALID_CREDENTIALS (mesmo erro em ambos os casos)

# Me — atualização parcial
Dado um usuário autenticado
Quando faço PATCH em /api/v1/auth/me/ enviando apenas name
Então recebo 200 e somente o campo name é alterado

# Me — deleção da conta
Dado um usuário autenticado com conversas e logs
Quando faço DELETE em /api/v1/auth/me/
Então recebo 204 e todos os dados dependentes são removidos em cascata
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Cadastro + login + perfil (`/me`) | Must | Caminho crítico de autenticação, pré-requisito de todas as demais rotas |
| Consentimento LGPD | Must | Requisito legal sem fallback (LGPD Art. 11) |
| Deleção em cascata | Must | Obrigação LGPD de remoção de dados sensíveis |
| Criação de usuário admin | Should | Operação administrativa de menor frequência |
| `persist_user_name` (captura via chat) | Should | Importante para onboarding, mas com fallback (perfil manual) |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/accounts/models.py` | `User`, `UserManager.create_user`, `UserManager.create_superuser` | 🟢 |
| `apps/accounts/serializers.py` | `RegisterSerializer`, `LoginSerializer`, `MeUpdateSerializer`, `AdminCreateUserSerializer`, `UserSerializer` | 🟢 |
| `apps/accounts/views.py` | `register`, `login`, `admin_create_user`, `me` | 🟢 |
| `apps/accounts/services/persist.py` | `persist_user_name` | 🟢 |
| `apps/accounts/urls.py` | rotas `/auth/register/`, `/auth/login/`, `/auth/me/` | 🟢 |
| `apps/audit/urls.py` | rota `/admin/users/` (admin_create_user) | 🟢 |

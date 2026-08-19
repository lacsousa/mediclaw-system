# Permissões e Papéis — MediClaw

> Gerado pelo **Detetive** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Artefato transversal — RBAC/ACL do sistema.

---

## 1. Papéis

| Papel | Criação | Permissões | Evidência |
|---|---|---|---|
| **USER** (médico) | `register` (padrão) | Dados de saúde do próprio escopo (pacientes, conversas, logs) | `ROLE_CHOICES`, `UserManager` 🟢 |
| **ADMIN** | `create_superuser` / `AdminCreateUserSerializer(role="ADMIN")` | Tudo de USER + criar usuários + métricas do dia | `IsAdminRole`, `welcome.py:29` 🟢 |
| **Anônimo (anon)** | — | Apenas `register`, `login`, `refresh` e `/health/` | `AllowAny` nas views; throttle anon 🟢 |

> Não há paciente como papel de acesso — `Patient` é entidade de dados, não ator. 🟢

---

## 2. Mecanismos de autorização

| Mecanismo | Como funciona | Uso | Evidência |
|---|---|---|---|
| **Autenticação global** | `DEFAULT_AUTHENTICATION_CLASSES = [JWTAuthentication]` | Todas as rotas (Bearer token) | settings.py:116-118 🟢 |
| **Permissão global** | `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` | Toda rota é privada por padrão | settings.py:119 🟢 |
| **Ownership por queryset** | Views filtram `doctor=request.user`; recurso alheio → `NOT_FOUND` (404), nunca `FORBIDDEN` | patients, conversations, health_logs | vários views 🟢 |
| **`IsAdminRole`** | `role == "ADMIN"` | criação de usuário, métricas | common/permissions.py:4-10 🟢 |
| **`IsOwner`** | owner = `doctor` \| `user` \| `uploaded_by` | **código morto** — nenhuma view usa | common/permissions.py:13-20 🟢 |
| **Throttling** | anon `30/min`, user `60/min`, chat `10/min` | global + `ChatThrottle` só em `post_message` | settings.py:127 🟢 |
| **Auth especial SSE** | AccessToken no query string `?token=` (EventSource não envia headers) | `GET /conversations/<id>/stream/` | conversations/views.py:120-151 🟡 |

---

## 3. Matriz de permissões por rota

> Convenção de código do PROJECT-CONTEXT.md: `INVALID_CREDENTIALS`, `MISSING_TOKEN`, `INVALID_TOKEN`, `FORBIDDEN`, `NOT_FOUND`, etc.

### 3.1 Autenticação e perfil

| Método | Rota | Auth | Permissão | Throttle | Evidência |
|---|---|---|---|---|---|
| POST | `/api/v1/auth/register/` | anon | `AllowAny` | anon 30/min | accounts/views.py:19-21 🟢 |
| POST | `/api/v1/auth/login/` | anon | `AllowAny` | anon 30/min | accounts/views.py:37-39 🟢 |
| POST | `/api/v1/auth/refresh/` | anon (refresh token) | JWT refresh | anon | config/urls.py, accounts/urls.py 🟢 |
| GET/PATCH/DELETE | `/api/v1/auth/me/` | Bearer | `IsAuthenticated` | user 60/min | accounts/views.py:66-68 🟢 |

### 3.2 Pacientes

| Método | Rota | Auth | Permissão | Ownership | Evidência |
|---|---|---|---|---|---|
| GET | `/api/v1/patients/` | Bearer | `IsAuthenticated` | `doctor=request.user` (lista) | patients/views.py:38-41 🟢 |
| GET | `/api/v1/patients/<id>/` | Bearer | `IsAuthenticated` | pk fora do escopo → 404 | patients/views.py:56-58 🟢 |
| PATCH | `/api/v1/patients/<id>/` | Bearer | `IsAuthenticated` | idem | patients/views.py:56 🟢 |
| DELETE | `/api/v1/patients/<id>/` | Bearer | `IsAuthenticated` | idem → cascade logs | patients/views.py:56 🟢 |

> **Não há** POST em pacientes (criação via chat). 🟢

### 3.3 Logs biométricos (health_logs)

| Método | Rota | Auth | Permissão | Ownership | Evidência |
|---|---|---|---|---|---|
| GET/POST/DELETE | `/api/v1/health/weight/` | Bearer | `IsAuthenticated` | `patient_id` + `doctor=request.user` | health_logs/views.py:19-24,34 🟢 |
| GET/POST/DELETE | `/api/v1/health/sleep/` | Bearer | `IsAuthenticated` | idem | idem 🟢 |
| GET/POST/DELETE | `/api/v1/health/activity/` | Bearer | `IsAuthenticated` | idem | idem 🟢 |
| GET/POST/DELETE | `/api/v1/health/nutrition/` | Bearer | `IsAuthenticated` | idem | idem 🟢 |
| GET | `/api/v1/health/summary/?patient_id=&window=` | Bearer | `IsAuthenticated` | `patient_id` obrigatório; ownership via queryset | health_logs/views.py:87-97 🟢 |

### 3.4 Conversas e mensagens

| Método | Rota | Auth | Permissão | Throttle | Evidência |
|---|---|---|---|---|---|
| GET/POST | `/api/v1/conversations/` | Bearer | `IsAuthenticated` | user 60/min | conversations/views.py:57-59 🟢 |
| GET/DELETE | `/api/v1/conversations/<id>/` | Bearer | `IsAuthenticated` | user 60/min | conversations/views.py:79-81 🟢 |
| POST | `/api/v1/conversations/<id>/messages/` | Bearer | `IsAuthenticated` | **chat 10/min** | conversations/views.py:103-105 🟢 |
| GET | `/api/v1/conversations/<id>/stream/` | **`?token=`** (AccessToken) | AccessToken válido | **nenhum** 🟡 | conversations/views.py:120 🟢 |

### 3.5 Knowledge Base (rag) e Admin

| Método | Rota | Auth | Permissão | Evidência |
|---|---|---|---|---|
| POST | `/api/v1/admin/knowledge/upload/` | Bearer | `IsAuthenticated` (qualquer usuário) | rag/views.py:23-24 🟡 |
| GET | `/api/v1/admin/knowledge/` | Bearer | `IsAuthenticated` (qualquer usuário) | rag/views.py:62-63 🟡 |
| GET | `/api/v1/admin/knowledge/<id>/status/` | Bearer | `IsAuthenticated` (qualquer usuário) | rag/views.py:71-72 🟡 |
| DELETE | `/api/v1/admin/knowledge/<id>/` | Bearer | `IsAuthenticated` (qualquer usuário) | rag/views.py:117-118 🟡 |
| GET | `/api/v1/admin/metrics/` | Bearer | **`IsAdminRole`** | rag/views.py:88-89 🟢 |
| POST | `/api/v1/admin/users/` | Bearer | **`IsAdminRole`** | accounts/views.py:56-57 🟢 |

### 3.6 Infraestrutura

| Método | Rota | Auth | Permissão | Evidência |
|---|---|---|---|---|
| GET | `/health/` | **nenhuma** | `AllowAny` | common/health_urls.py, views.py:19 🟢 |
| GET | `/swagger/`, `/redoc/`, `/swagger.json` | **nenhuma** | `AllowAny` (drf_yasg public) | config/urls.py:7-18 🟢 |

---

## 4. Regras de acesso a dados (object-level)

| Recurso | Regra de acesso | Mecanismo | Evidência |
|---|---|---|---|
| `Patient` | Só do médico dono | queryset `doctor=request.user` | patients/views.py 🟢 |
| Logs biométricos | Só do dono do `patient_id` | mixin + queryset filtrada | health_logs/views.py 🟢 |
| `Conversation` | Só do médico dono; paciente alheio vira 404 | queryset `doctor=request.user` | conversations/views.py 🟢 |
| `Message` | Herda o acesso da conversa (via FK) | queryset da conversa | conversations/views.py 🟢 |
| `KnowledgeDocument` | **Sem ownership**: qualquer autenticado lista/deleta qualquer documento | queryset sem filtro | rag/views.py:64, 74 🟡 |
| Métricas | Apenas `ADMIN` | `IsAdminRole` | rag/views.py:89 🟢 |

---

## 5. Gaps e riscos de permissão

| # | Risco | Detalhe | Evidência |
|---|---|---|---|
| P1 | **KB aberta a qualquer usuário autenticado** | Upload/delete de documentos não exigem `IsAdminRole`, embora a rota esteja sob `/api/v1/admin/`. Qualquer médico pode injetar conteúdo que alimenta as respostas do chat (risco de prompt/content poisoning). | rag/views.py:23-24, 117-118 🟡 |
| P2 | **Stream sem throttle** | O caminho mais usado pelo frontend não tem `ChatThrottle` (10/min) — só `post_message` tem. Custo LLM sem limite efetivo. | conversations/views.py:120, 103-105 🟢 |
| P3 | **Auth via query string no stream** | `?token=` aparece em logs de proxy/access log (Nginx). Necessário para EventSource, mas é vazamento potencial de credencial em log. | conversations/views.py:120-151 🟡 |
| P4 | **`IsOwner` morto** | Existe mas não é usado; o padrão de facto é filtro de queryset. Unificar no futuro (Architect). | common/permissions.py:13 🟢 |
| P5 | **Exceção catch-all no stream** | `except (TokenError, Exception)` mascara erros de programação como "Token inválido". | conversations/views.py:142 🟢 |
| P6 | **Papel imutável via API** | Nenhum endpoint promove/degrada role; operação administrativa depende de acesso manual. | accounts/serializers.py 🟢 |

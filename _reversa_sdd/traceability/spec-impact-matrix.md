# Spec Impact Matrix — MediClaw

> Gerado pelo **Arquiteto** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> **Qual componente impacta qual.** Derivado das dependências extraídas em `code-analysis.md` (seção *Dependências* de cada módulo) e da topologia de produção (ADR-006).

---

## 1. Matriz de impacto entre componentes

Leitura: a **linha** `X` impacta a **coluna** `Y` quando uma mudança em `X` tem efeito em `Y`. `●` = dependência direta (impacto imediato); `○` = dependência transitiva/indireta.

| Componente (linha) → | accounts | patients | health_logs | conversations | ai_engine | rag | audit | common | Painel React | Infra (Nginx/Compose) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **accounts** | — | ● | ○ | ● | ○ | ○ | ● | ○ | ● | — |
| **patients** | ● | — | ● | ● | ● | — | — | ○ | ● | — |
| **health_logs** | — | ● | — | ○ | ● | — | — | ○ | ● | — |
| **conversations** | ● | ● | ○ | — | ● | ● | ● | ○ | ● | — |
| **ai_engine** | ○ | ● | ● | ● | — | ● | ● | ● | ● | — |
| **rag** | ● | — | ○ | ● | ● | — | ● | ● | ● | — |
| **audit** | — | — | — | — | — | — | — | ○ | — | — |
| **common** | ● | ● | ● | ● | ● | ● | ● | — | ● | — |
| **Painel React** | ● | ● | ● | ● | ● | ● | ● | — | — | — |
| **Infra (Nginx/Compose)** | — | — | — | ○ | — | ○ | — | ○ | ● | — |

> **Legenda:** `●` impacto direto (chamada de serviço, import, contrato de rota ou contrato de payload). `○` impacto indireto (ex.: via `common` ou via cadeia de cascade/queryset). `—` sem dependência identificada.

---

## 2. Justificativas por componente

### 2.1 `accounts` (User, auth JWT)

| Impacta | Como |
|---|---|
| `patients`, `conversations` | `User.delete()` cascata (LGPD); ownership via `doctor_id` |
| `common` | `AUTH_USER_MODEL`, `IsAdminRole`, autenticação global |
| `audit` | `record("USER_REGISTERED"\|"LOGIN"\|"ADMIN_CREATED_USER")` |
| `conversations` | `ensure_welcome_conversation` no register |
| `rag` | métricas (`users_total`) + `KnowledgeDocument.uploaded_by` |

### 2.2 `patients`

| Impacta | Como |
|---|---|
| `health_logs` | logs apontam `patient_id` (CASCADE) |
| `conversations` | `Conversation.patient` (SET_NULL) e título via nome |
| `ai_engine` | captura chama `ensure_or_create_patient`/`resolve_patient_dob` |
| `accounts` | FK `doctor` (CASCADE na exclusão) |

### 2.3 `health_logs`

| Impacta | Como |
|---|---|
| `ai_engine` | `persist_*` (captura) e `summarize` (skill `health_summary`) |
| `patients` | anotação `latest_weight_kg` |
| `conversations` | `summarize` alimenta o prompt do chat |

### 2.4 `conversations` (núcleo de transporte)

| Impacta | Como |
|---|---|
| `ai_engine` | chama `orchestrator.generate/generate_stream`; contrato de eventos SSE |
| `accounts` | welcome no register; `User` cascade |
| `patients` | vínculo paciente↔conversa |
| `rag` | métricas (`conversations_total`, `messages_today`, `tokens_today`) |
| `audit` | eventos `GUARDRAIL_BLOCKED`/`MESSAGE_SENT` (via orchestrator) |
| Painel | contrato de payloads e streaming SSE |

### 2.5 `ai_engine` (núcleo de IA)

| Impacta | Como |
|---|---|
| `rag` | `retriever.search` para contexto científico |
| `health_logs` | persiste logs capturados; lê `summarize` |
| `patients` | cria/resolve paciente na captura |
| `conversations` | gera a resposta persistida em `Message` |
| `audit` | eventos de guardrail/mensagem |
| `common` | `AppError`, `LLMProviderError` (502) |
| Painel | modos de onboarding, citações, `data_capture` em metadata |

### 2.6 `rag`

| Impacta | Como |
|---|---|
| `ai_engine` | injeta chunks com citações no prompt |
| `accounts` | `uploaded_by`; métricas de usuários |
| `conversations` | métricas diárias |
| `audit` | `record("KB_UPLOAD"\|"KB_DELETE")` |
| Painel | `/admin/knowledge/*` e `/admin/metrics/` |

### 2.7 `audit`

| Impacta | Como |
|---|---|
| `common` | padrões de erro/log |
| — | `record()` é stub `pass` — **nada persiste**; impacto real só no Epic 3 (ADR-007) 🔴 |

### 2.8 `common` (infra transversal)

| Impacta | Como |
|---|---|
| **todos os apps** | envelope, exception handler, permissions, middleware, paginação, logging |
| Painel | formato `{data, error, meta}` e códigos de erro |
| Infra | `/health/` usado pelo healthcheck do Docker |

### 2.9 Painel React

| Impacta | Como |
|---|---|
| todos os apps (via API) | contrato de payloads consumidos |
| `accounts` | fluxo de login/cadastro/refresh |
| `conversations` | usa `stream/` como caminho principal (throttle ausente → custo) |
| `rag` | gestão de KB e métricas |

### 2.10 Infra (Nginx/Compose)

| Impacta | Como |
|---|---|
| Painel | build arg `NEXT_PUBLIC_API_URL`; proxy para `:3001` |
| `conversations` | `?token=` exposto em access log (P3) |
| `rag`/`common` | `/static/` servido pelo Nginx; healthcheck com headers |

---

## 3. Especificações de alta sensibilidade (mudanças com maior raio de impacto)

| # | Área | Por quê |
|---|---|---|
| S1 | **`ai_engine` + `conversations`** | Núcleo do produto; contrato SSE (eventos `citation`/`token`/`done`/`error`) é acoplado ao frontend |
| S2 | **`common`** | Mudança no envelope/códigos de erro afeta **toda** a API e o cliente React |
| S3 | **Modelo `User` / cascade** | Alterações de `on_delete` ou RBAC têm efeito LGPD e de ownership em todos os domínios |
| S4 | **`rag`** | A KB alimenta o chat; mudança de threshold/embedding altera o comportamento das respostas |
| S5 | **Endpoints de paginação manual** | `patients` e `conversations` divergem do padrão global — risco de duplicar lógica ao evoluir |

---

## 4. Componentes acoplados a dívidas conhecidas

| Componente | Dívida(s) relacionada(s) | Referência |
|---|---|---|
| `conversations` | D4 (stream sem throttle), D7 (código de erro), D8 (MAX_MESSAGES), D10 (catch-all), D13 (serialização manual) | `architecture.md` §5 |
| `ai_engine` | D10 (catch-all), D11 (`patient_created`), D12 (tokens no stream), D15 (`os.getenv`) | `architecture.md` §5 |
| `rag` | D3 (KB aberta), D16 (ingestão síncrona), D17 (sem retry) | `architecture.md` §5 |
| `audit` | D2 (stub, sem ActivityLog) | `architecture.md` §5 |
| Painel + `conversations` | D5 (token no query string) | `permissions.md` P3 |

---

## 5. Matriz de rastreabilidade com as specs do domínio

As regras de negócio do domínio (`domain.md` §4, R1–R55) mapeiam para os componentes:

| Domínio | Regras | Componente principal |
|---|---|---|
| Identidade e acesso | R1–R7 | `accounts` (+ `conversations` para R6) |
| Pacientes e dedup | R8–R13 | `patients` |
| Logs biométricos | R14–R21 | `health_logs` |
| Conversas e mensagens | R22–R29 | `conversations` |
| Guardrails e prompts | R30–R39 | `ai_engine` |
| Captura automática | R40–R45 | `ai_engine` (+ `health_logs`, `patients`) |
| Knowledge Base/RAG | R46–R52 | `rag` (+ `ai_engine`) |
| Auditoria | R53–R55 | `audit` |

---

*Matriz derivada das dependências reais extraídas em `code-analysis.md`. Em futuras gerações do Writer, cada spec SDD deve referenciar esta matriz para identificar componentes impactados.*

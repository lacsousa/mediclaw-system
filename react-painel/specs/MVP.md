# MediClaw — Especificação Funcional e Técnica do MVP (Frontend)

> Versão: 1.0 | Data: 2026-05-14 | Status: Rascunho
> **Escopo deste documento:** Frontend (Next.js + Chakra UI). Backend Django é API externa.

---

## 1. Visão Geral do Produto

### Posicionamento

O painel MediClaw é a interface web que permite ao usuário registrar dados biométricos, conversar com a IA e acompanhar seu progresso de longevidade. Consome exclusivamente as APIs REST e SSE do backend Django.

> O painel **não processa lógica de negócio nem IA**. Toda validação crítica, guardrails e geração de conteúdo ocorrem no backend.

### Personas Primárias

| Persona           | Descrição                         | Principal necessidade                                      |
| ----------------- | --------------------------------- | ---------------------------------------------------------- |
| **Usuário Final** | Adulto interessado em longevidade | Interface clara para registrar dados e conversar com a IA  |
| **Administrador** | Gestor da plataforma              | Gerenciar base de conhecimento e monitorar métricas de uso |

---

## 2. Funcionalidades Principais (MVP — Frontend)

### 2.1 Autenticação

- Tela de cadastro com e-mail, senha e aceite de termos LGPD
- Tela de login com JWT (access + refresh)
- Renovação automática do access token via interceptor Axios
- Proteção de rotas privadas com redirect para `/login`

### ~~2.2 Dashboard~~ — DESCONTINUADO

> **Pivot (2026-05-27):** A tela `/dashboard` foi removida. Após o login, o usuário é redirecionado diretamente para `/chat` — a interface de conversação é a tela principal do produto.

### ~~2.3 Logs de Saúde~~ — DESCONTINUADO

> **Pivot (2026-05-27):** Os formulários manuais de entrada de dados biométricos (`/health/*`) foram removidos. O backend extrai dados de saúde automaticamente via NLP das mensagens de chat (`capture_from_message`).

### 2.4 Chat com IA

- Lista de conversas com título e data da última mensagem
- Interface de chat com bolhas de mensagem (usuário e assistente)
- Streaming token a token via SSE
- Indicador visual quando a resposta é bloqueada pelo guardrail
- Citações de fonte exibidas abaixo da resposta
- Disclaimer médico visível em toda resposta do assistente

### ~~2.5 Perfil do Usuário~~ — DESCONTINUADO

> **Pivot (2026-05-27):** A página `/profile` foi removida. Nome, altura, sexo biológico e data de nascimento são coletados durante o onboarding conversacional (`ensure_welcome_conversation`).

### 2.6 Painel Admin (role ADMIN)

- Upload de documentos (PDF, MD, TXT) para a base de conhecimento
- Listagem de documentos com status de indexação (polling)
- Remoção de documentos
- Métricas de uso: usuários, conversas, mensagens, tokens, bloqueios de guardrail

---

## 3. Arquitetura da Solução

### Visão Geral

```
┌──────────────────────────────────────────────────────┐
│                  Browser (Next.js)                   │
│                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ auth pages │  │ health pages │  │  chat page  │  │
│  └─────┬──────┘  └──────┬───────┘  └──────┬──────┘  │
│        │                │                 │          │
│        └────────────────┴─────────────────┘          │
│                         │                            │
│              ┌───────────▼──────────┐                │
│              │    AuthContext       │                │
│              │   + api.ts (Axios)   │                │
│              └───────────┬──────────┘                │
└──────────────────────────┼───────────────────────────┘
                           │ REST + SSE
          ┌────────────────▼───────────────────┐
          │     Django Backend (localhost:8000) │
          └────────────────────────────────────┘
```

### Decisões Arquiteturais

| Decisão     | Escolha                  | Justificativa                                                  |
| ----------- | ------------------------ | -------------------------------------------------------------- |
| Framework   | Next.js 15 App Router    | SSR/SSG disponível; estrutura de rotas por pasta               |
| UI          | Chakra UI v3             | Já configurado; acessibilidade nativa; tema customizável       |
| HTTP        | Axios com interceptors   | Renova token 401 automaticamente; envelope de erro consistente |
| Estado Auth | React Context            | Suficiente para MVP; evita overhead do Redux                   |
| Streaming   | EventSource (SSE nativo) | Suportado pelo backend; sem dependência extra                  |
| Storage JWT | `localStorage`           | Simples para MVP; migrar para `httpOnly` cookie na fase 2      |

---

## 4. Estrutura de Rotas

| Rota               | Acesso  | Descrição                                     |
| ------------------ | ------- | --------------------------------------------- |
| `/`                | Público | Redireciona para `/chat` ou `/login`          |
| `/login`           | Público | Formulário de login                           |
| `/register`        | Público | Formulário de cadastro                        |
| `/chat`            | Privado | Lista de conversas (tela principal pós-login) |
| `/chat/[id]`       | Privado | Interface de chat com streaming SSE           |
| `/patients`        | Privado | Lista de pacientes do médico (Epic 7)         |
| `/patients/[id]`   | Privado | Detalhe do paciente: perfil + saúde (Epic 7)  |
| `/admin/knowledge` | Admin   | Gestão da base de conhecimento                |
| `/admin/metrics`   | Admin   | Métricas e logs de auditoria                  |

---

## 5. Fluxos do Usuário

### 5.1 Cadastro e Login

```
/register → Formulário (email, senha, nome, aceite)
          → POST /api/v1/auth/register
          → Armazena access_token + refresh_token em localStorage
          → Redirect /chat

/login    → Formulário (email, senha)
          → POST /api/v1/auth/login
          → Armazena tokens
          → Redirect /chat
```

### 5.2 Renovação de Token (Interceptor)

```
Request com access_token expirado → 401 do backend
→ Interceptor Axios captura 401
→ POST /api/v1/auth/refresh com refresh_token
→ Armazena novo access_token
→ Reenvia request original
→ Se refresh expirado → logout + redirect /login
```

### 5.3 Chat com Streaming

```
/chat/[id]
→ Usuário digita mensagem → submit
→ EventSource conecta em /api/v1/conversations/{id}/stream?prompt=...&token=<jwt>
→ Eventos "token" acumulados em estado local → renderização progressiva
→ Evento "citation" exibe fonte abaixo da bolha
→ Evento "done" fecha SSE + persiste no histórico
→ Evento "error" exibe toast e fecha SSE
→ Se blocked=true na resposta → badge "Bloqueado" + mensagem educativa
```

### 5.4 Upload de Documento (Admin)

```
/admin/knowledge
→ Drag-and-drop ou file picker (PDF/MD/TXT, ≤10MB)
→ POST /api/v1/admin/knowledge/upload (multipart)
→ Documento aparece na tabela com status "PROCESSING"
→ Polling GET /api/v1/admin/knowledge/{id}/status a cada 3s
→ Status muda para "INDEXED" ou "ERROR" → polling para
```

---

## 6. Roadmap

### Fase 1 — MVP (0–3 meses)

- [x] Foundation Next.js + Chakra + Axios
- [x] Auth (login, cadastro, refresh automático)
- [x] ~~Dashboard com summary~~ (descontinuado — pivot)
- [x] ~~CRUD de logs de saúde~~ (descontinuado — pivot; dados capturados via chat)
- [x] Chat com streaming SSE
- [x] ~~Perfil do usuário~~ (descontinuado — pivot; dados coletados conversacionalmente)
- [x] Painel admin (KB + métricas) — polling de status e logs de auditoria pendentes

### Fase 2 — Consolidação (3–6 meses)

- [ ] Migrar JWT de localStorage para httpOnly cookie
- [ ] Gráficos de evolução (peso, sono, atividade ao longo do tempo)
- [ ] PWA / notificações (lembrete de registro)
- [ ] Dark mode

### Fase 3 — Escala (6–12 meses)

- [ ] Internacionalização (i18n)
- [ ] App mobile (React Native ou Flutter)

---

_Próximo documento: [PRD.md](PRD.md)_

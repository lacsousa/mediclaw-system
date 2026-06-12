# MediClaw — Architecture Document (Frontend)

> Versão: 1.0 | Data: 2026-05-14
> Referência: [MVP.md](MVP.md) | [PRD.md](PRD.md) | [TASKS.md](TASKS.md)
> **Escopo:** Frontend Next.js. Backend Django é API externa.

---

## Visão Geral

SPA híbrida (Next.js App Router) que consome REST e SSE do backend Django. Todo estado de servidor é buscado pelo cliente; não há server actions nem server components com fetch de dados de negócio no MVP — simplifica o modelo mental e facilita a transição para um eventual app mobile.

```
Browser
  │
  ├── App Router (src/app/)
  │     ├── page.tsx              → Landing page (pública)
  │     ├── (auth)/login          → LoginForm
  │     ├── (auth)/register       → RegisterForm
  │     └── (app)/                → RequireAuth
  │           ├── chat/[id]       → ChatWindow (SSE)
  │           ├── admin/knowledge → KnowledgeTable + file picker (RequireAdmin)
  │           └── admin/metrics   → MetricsCards (RequireAdmin)
  │
  ├── Context Layer
  │     ├── AuthContext           → token, user, isAuthenticated
  │     └── ToastContext          → notificações globais
  │
  └── lib/api.ts (Axios)          → interceptors JWT
        │
        └── HTTP / SSE ──────────▶  Django Backend (localhost:8000)
```

---

## Architectural Decision Records (ADRs)

### ADR-01: Next.js App Router sem Server Components de negócio

- **Decisão:** Todas as chamadas de API ocorrem no cliente (hooks + Axios), não em Server Components
- **Por quê:** Backend já serve a API; duplicar fetch no servidor Next.js aumenta complexidade sem benefício no MVP
- **Trade-off:** Sem SSR de dados de negócio; SEO não é requisito para um painel autenticado
- **Migração:** Fase 2 pode usar Server Components para rotas públicas (landing, docs)

### ADR-02: Chakra UI v3 como sistema de design

- **Decisão:** Chakra UI v3 com tema padrão + customizações mínimas
- **Por quê:** Já configurado no projeto; acessibilidade nativa; componentes prontos (Modal, Toast, Drawer)
- **Trade-off:** Bundle maior que Tailwind; justificado pelo ganho de produtividade no MVP
- **Alternativa descartada:** Tailwind — exigiria construir todos os componentes compostos do zero

### ADR-03: JWT em localStorage (MVP)

- **Decisão:** `access_token` e `refresh_token` em `localStorage`
- **Por quê:** Simples de implementar; sem necessidade de rota de API Next.js para cookie proxy
- **Trade-off:** Vulnerável a XSS; mitigado pela ausência de `dangerouslySetInnerHTML` com input do usuário
- **Migração:** Fase 2 → `httpOnly` cookies via middleware Next.js e rota de token proxy

### ADR-04: React Context para estado de auth

- **Decisão:** `AuthContext` com `useState`; sem Redux, Zustand ou Jotai
- **Por quê:** Estado de auth é global mas simples (user + tokens); Context é suficiente no MVP
- **Trade-off:** Re-renders desnecessários se o contexto crescer; aceitável com os dados atuais
- **Migração:** Zustand se o estado global crescer além de auth + toast

### ADR-05: EventSource nativo para SSE

- **Decisão:** `EventSource` nativo do browser, encapsulado em `@/lib/sse.ts`
- **Por quê:** Zero dependências extras; suportado por todos os browsers modernos
- **Trade-off:** `EventSource` não suporta headers → token via query string (risco menor que XSS em `dangerouslySetInnerHTML`)
- **Wrapper:** `lib/sse.ts` abstrai `EventSource` com callbacks `onToken`, `onCitation`, `onDone`, `onError`

### ADR-06: Polling para status de indexação RAG (pendente)

- **Decisão:** `setInterval` de 3s em `GET /api/v1/admin/knowledge/{id}/status` enquanto `status === "PROCESSING"`
- **Status:** Não implementado ainda. A tabela de documentos mostra o status no momento do carregamento mas não faz polling automático.
- **Por quê:** Backend MVP não emite SSE para admin; polling é simples e suficiente
- **Trade-off:** Carga extra no servidor; ok para volume baixo do MVP
- **Migração:** Fase 2 → SSE de status ou WebSocket

---

## Stack Detalhada

| Camada      | Tecnologia            | Versão               |
| ----------- | --------------------- | -------------------- |
| Framework   | Next.js               | 16.x (App Router)    |
| Linguagem   | TypeScript            | 5.x (strict)         |
| UI          | Chakra UI             | v3.x                 |
| HTTP        | Axios                 | 1.x                  |
| Estado      | React Context + hooks | (built-in)           |
| SSE         | EventSource           | (browser nativo)     |
| Lint        | ESLint                | next/core-web-vitals |
| Gerenciador | npm                   | 10.x                 |

---

## Estrutura de Módulos

```
src/
├── app/
│   ├── layout.tsx              # Root layout: ChakraProvider + AuthContext + ToastContext
│   ├── page.tsx                # Landing page pública; redireciona para /chat se autenticado
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (app)/                  # Grupo autenticado (RequireAuth)
│       ├── layout.tsx
│       ├── chat/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── patients/               # Epic 7
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       └── admin/
│           ├── knowledge/page.tsx  # RequireAdmin
│           └── metrics/page.tsx    # RequireAdmin
│
├── components/
│   ├── layout/
│   │   ├── PageShell.tsx       # Wrapper: sidebar + topbar + <main>
│   │   ├── Sidebar.tsx         # "Chat IA" nav link; brand "MediClaw / Assistente de saúde"
│   │   └── TopBar.tsx          # Nome do usuário, logout
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── RequireAuth.tsx     # Redireciona para /login se não autenticado
│   │   └── RequireAdmin.tsx    # Redireciona para /chat se role !== "ADMIN"
│   ├── chat/
│   │   ├── MessageBubble.tsx   # Bolha usuário ou assistente; disclaimer deduplication
│   │   ├── ChatInput.tsx       # Input + submit + controle SSE
│   │   ├── ConversationItem.tsx # Item na lista: mostra patient.first_name ou "Nova conversa"
│   │   └── CitationBadge.tsx
│   ├── patients/               # Epic 7
│   │   ├── PatientTable.tsx    # Lista com nome, último atend., consultas, peso, IMC
│   │   ├── PatientHeader.tsx   # Detalhe: nome, DOB, sexo, altura, IMC
│   │   ├── PatientConversations.tsx
│   │   └── PatientHealthTabs.tsx
│   └── common/
│       └── FullPageSpinner.tsx
│
├── context/
│   ├── AuthContext.tsx         # { user, isAuthenticated, isLoading, login, logout }
│   └── ToastContext.tsx        # { showToast(msg, status) }
│
├── hooks/
│   ├── useConversations.ts     # GET/POST/DELETE conversas (paginado)
│   ├── useMessages.ts          # GET mensagens de uma conversa
│   ├── usePatients.ts          # GET /patients (paginado) + GET /patients/{id}  (Epic 7)
│   ├── useAdminKnowledge.ts    # Upload, listagem, delete (admin)
│   └── useAdminMetrics.ts      # GET /admin/metrics
│
├── lib/
│   ├── api.ts                  # Instância Axios + interceptors JWT
│   ├── auth.ts                 # login(), logout(), refreshToken()
│   ├── sse.ts                  # openStream(url, callbacks) → () => void (cleanup)
│   └── chat-disclaimer.ts      # hasEducationalDisclaimer(text): boolean
│
└── types/
    └── api.ts                  # ApiResponse<T>, User (first_name), AdminMetrics, etc.
```

---

## Fluxo de Autenticação (Interceptor)

```
┌──────────────────────────────────────────────────────┐
│ Request Interceptor                                  │
│   token = localStorage.getItem("access_token")      │
│   if (token) headers.Authorization = "Bearer " + token│
└─────────────────────┬────────────────────────────────┘
                      ▼
              Backend responde
                      │
            ┌─────────┴──────────┐
            │ 200 OK             │ 401 Unauthorized
            ▼                   ▼
        Retorna data     Response Interceptor
                              │
                    POST /auth/refresh
                              │
                   ┌──────────┴──────────┐
                   │ 200 OK              │ 401 (refresh expirado)
                   ▼                    ▼
           Salva novo token      clearStorage() + redirect /login
           Reenvia request
```

---

## Fluxo SSE (Chat)

```
ChatInput.submit()
    │
    ├── Salva mensagem do usuário no estado local (otimistic)
    │
    └── lib/sse.openStream(
            `/api/v1/conversations/${id}/stream?prompt=<enc>&token=<jwt>`,
            {
              onToken:    (t) => setPartialReply(prev => prev + t),
              onCitation: (c) => setCitations(prev => [...prev, c]),
              onDone:     (d) => { setReplying(false); fetchMessages() },
              onError:    (e) => { showToast(e.message, "error"); setReplying(false) }
            }
        )
    │
    EventSource abre GET com token na query
    Eventos chegam → callbacks disparam setState
    Evento "done" → fecha EventSource + recarrega histórico
```

---

## Tipos TypeScript Principais

```typescript
// src/types/api.ts

export interface ApiResponse<T> {
  data: T | null;
  error: { code: string; message: string } | null;
  meta: { total?: number; page?: number } | null;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  role: "USER" | "ADMIN";
  accepted_terms_at: string | null;
  profile: {
    birth_date: string | null;
    biological_sex: "M" | "F" | "OTHER" | null;
    height_cm: number | null;
  } | null;
}

export interface Patient {
  id: number;
  first_name: string;
  birth_date: string | null;
  biological_sex: "M" | "F" | "OTHER" | null;
  height_cm: number | null;
  conversation_count: number;
  last_seen_at: string | null;
  latest_weight_kg: number | null;
}

export interface Conversation {
  id: number;
  title: string;
  patient: { id: number; first_name: string } | null; // Epic 7
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  tokens_used: number | null;
  blocked_by_guardrail: boolean;
  metadata: { citations?: Citation[] };
  created_at: string;
}

export interface Citation {
  source: string;
  chunk_id: string;
}

export interface AdminMetrics {
  users_total: number;
  conversations_total: number;
  messages_today: number;
  tokens_today: number;
  guardrail_blocks_today: number;
  kb_documents_indexed: number;
}

export interface KnowledgeDocument {
  id: number;
  title: string;
  status: "PROCESSING" | "INDEXED" | "ERROR";
  chunk_count: number | null;
  created_at: string;
}
```

---

## Segurança

| Vetor          | Mitigação                                                                                           |
| -------------- | --------------------------------------------------------------------------------------------------- |
| XSS            | Sem `dangerouslySetInnerHTML`; conteúdo da IA renderizado como texto simples ou Markdown sanitizado |
| Token exposure | Sem log de token no console; sem token em URL persistida (só em SSE temporária)                     |
| CSRF           | API stateless com JWT; sem cookies de sessão no MVP                                                 |
| Clickjacking   | `X-Frame-Options: DENY` via `next.config.ts` headers                                                |
| Dependências   | `npm audit` no CI                                                                                   |

---

## Observabilidade

- Erros de requisição capturados no interceptor e exibidos via `ToastContext`
- Console errors em desenvolvimento; silenciados em produção via variável de ambiente
- Fase 2: integração com Sentry para error tracking

---

_Próximo documento: [TASKS.md](TASKS.md)_

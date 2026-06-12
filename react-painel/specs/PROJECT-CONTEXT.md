# MediClaw — Project Context (Frontend)

> Arquivo de contexto para agentes de IA e desenvolvedores.
> Leia este arquivo antes de qualquer implementação.
> **Escopo:** Frontend (Next.js + Chakra UI + Axios). O Backend Django é tratado como API externa.

---

## O que é o MediClaw

Assistente de saúde com IA. Este repositório contém o painel web (React/Next.js) que consome as APIs REST e SSE expostas pelo backend Django em `http://localhost:8000/api/v1/`. **Dados biométricos são capturados automaticamente das mensagens de chat — não há formulários manuais de logs de saúde.**

**Restrição crítica:** O frontend **NUNCA** exibe diagnósticos médicos como fatos. Toda resposta da IA vem acompanhada de disclaimer visível. O painel deve tornar os guardrails do backend transparentes ao usuário.

---

## Stack (não negociável no MVP)

| Camada                 | Tecnologia                                | Notas                         |
| ---------------------- | ----------------------------------------- | ----------------------------- |
| Framework              | Next.js 16 (App Router)                   | `src/app/` como raiz de rotas |
| UI                     | Chakra UI v3                              | Sem Tailwind; sem MUI         |
| HTTP Client            | Axios (instância `@/lib/api`)             | Interceptors para JWT         |
| Linguagem              | TypeScript                                | Strict mode                   |
| Estado Global          | React Context + `useState` / `useReducer` | Sem Redux no MVP              |
| Streaming              | `EventSource` (SSE nativo)                | Para o chat em tempo real     |
| Gerenciador de pacotes | npm                                       | `package-lock.json` commitado |
| Lint                   | ESLint (config Next.js)                   | `eslint.config.mjs`           |
| Env                    | `NEXT_PUBLIC_*` via `.env.local`          | Nunca expor segredos          |

---

## Backend — Contrato de API

Base URL: `http://localhost:8000/api/v1/` (dev) — via `NEXT_PUBLIC_API_URL`.

Todas as respostas seguem o envelope:

```json
// Sucesso
{ "data": { "...": "..." }, "error": null, "meta": { "total": 10, "page": 1 } }

// Erro
{ "data": null, "error": { "code": "SNAKE_CASE_CODE", "message": "Mensagem legível" } }
```

Autenticação: `Authorization: Bearer <access_token>` em todas as rotas privadas.

Endpoints disponíveis:

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
PATCH  /api/v1/auth/me

GET/POST  /api/v1/conversations/
GET       /api/v1/conversations/{id}/
DELETE    /api/v1/conversations/{id}/
GET       /api/v1/conversations/{id}/stream  (SSE, auth via ?token=)

GET    /api/v1/admin/knowledge/          # base RAG compartilhada — IsAuthenticated
POST   /api/v1/admin/knowledge/upload    # qualquer usuário autenticado (PDF/MD/TXT)
GET    /api/v1/admin/knowledge/{id}/status
DELETE /api/v1/admin/knowledge/{id}

GET    /api/v1/admin/metrics             # admin-only (IsAdminRole)

GET    /health
```

> Os endpoints `/api/v1/health/*` existem no backend mas **não são consumidos pelo frontend**. Dados biométricos chegam ao backend via `capture_from_message()` ao processar mensagens de chat.

---

## Estrutura do Projeto

```
src/
├── app/                        # App Router (Next.js 16)
│   ├── layout.tsx              # Root layout com providers
│   ├── page.tsx                # Landing page pública; redireciona para /chat se autenticado
│   ├── (auth)/                 # Grupo sem sidebar
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (app)/                  # Grupo autenticado (RequireAuth no layout)
│       ├── layout.tsx
│       ├── chat/
│       │   ├── page.tsx        # Lista de conversas
│       │   └── [id]/page.tsx   # Chat com SSE
│       ├── patients/          # Gestão de pacientes
│       ├── conhecimento/page.tsx   # Base de conhecimento RAG (qualquer usuário autenticado)
│       └── admin/
│           └── metrics/page.tsx    # Métricas (RequireAdmin)
├── components/
│   ├── layout/                 # Sidebar ("Chat IA"), TopBar, PageShell
│   ├── auth/                   # LoginForm, RegisterForm, RequireAuth, RequireAdmin
│   ├── chat/                   # MessageBubble, ChatInput, CitationBadge
│   └── common/                 # FullPageSpinner, DeleteConfirmModal
├── lib/
│   ├── api.ts                  # Instância axios com interceptors JWT
│   ├── auth.ts                 # Funções login/logout/refresh
│   ├── sse.ts                  # Wrapper EventSource para o chat
│   └── chat-disclaimer.ts      # hasEducationalDisclaimer(text): boolean
├── context/
│   ├── AuthContext.tsx         # Token, user, isAuthenticated
│   └── ToastContext.tsx        # Notificações globais
├── hooks/
│   ├── useConversations.ts
│   ├── useMessages.ts
│   ├── useAdminKnowledge.ts
│   └── useAdminMetrics.ts
└── types/
    └── api.ts                  # Types TS: User (first_name, role, profile), AdminMetrics, etc.
```

---

## Convenções de Código

- **Componentes:** PascalCase, um por arquivo. Sem default export em arquivos com múltiplos exports.
- **Hooks:** prefixo `use`, retornam `{ data, isLoading, error }` no padrão SWR-like.
- **Chamadas HTTP:** sempre via instância `api` de `@/lib/api` — nunca `fetch` direto.
- **Tokens JWT:** armazenados em `localStorage` (`access_token`, `refresh_token`). Interceptor injeta header e renova automaticamente em 401.
- **Erros:** extrair `error.code` do envelope e mapear para mensagem amigável em português.
- **Variáveis de ambiente:** apenas `NEXT_PUBLIC_*` no cliente. Nunca expor chaves privadas.
- **Routing:** rotas privadas verificam `isAuthenticated` via `AuthContext`; redirecionam para `/login` se não autenticado.
- **Rotas admin:** verificam `user.role === "ADMIN"` além de autenticação.
- **Type hints:** obrigatório em props de componentes e retornos de hooks.
- **Comentários:** apenas quando o "porquê" não é óbvio.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`).

---

## Streaming SSE (Chat)

O chat usa `EventSource` nativo do browser. Como `EventSource` não suporta headers customizados, o token JWT é enviado via query string com TTL curto:

```
GET /api/v1/conversations/{id}/stream?prompt=<encoded>&token=<access_jwt>
```

Eventos recebidos:

```json
{ "type": "token",    "content": "..." }
{ "type": "citation", "source": "...", "chunk_id": "..." }
{ "type": "done",     "tokens_used": 142, "blocked": false }
{ "type": "error",    "code": "...", "message": "..." }
```

O componente `ChatInput` acumula tokens em estado local e renderiza a bolha progressivamente.

---

## Segurança — Checklist por Feature

Antes de fazer merge:

- [ ] Nenhuma chave privada ou secret exposta em `NEXT_PUBLIC_*` ou bundle
- [ ] Tokens JWT não logados no console em produção
- [ ] Inputs de formulário com validação client-side (além da server-side do backend)
- [ ] XSS: nunca usar `dangerouslySetInnerHTML` com conteúdo do usuário
- [ ] Links externos com `rel="noopener noreferrer"`
- [ ] Rotas privadas verificam autenticação antes de renderizar

---

## LGPD — Responsabilidades do Frontend

- Exibir o disclaimer médico da IA de forma visível em todas as respostas do chat
- Apresentar o termo de aceite de forma explícita no formulário de cadastro (`accept_terms=true` obrigatório)
- Não armazenar conteúdo de mensagens em `localStorage` ou `sessionStorage`
- Implementar botão de exclusão de conta que chama `DELETE /api/v1/auth/me`

---

## Variáveis de Ambiente (`.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/
```

---

## Como Rodar Localmente

```bash
# Pré-requisito: backend Django rodando em localhost:8000
npm install
cp .env.local.example .env.local   # ou criar manualmente
npm run dev
# Acesse http://localhost:3000
```

---

_Este arquivo deve ser lido por qualquer agente ou desenvolvedor antes de iniciar trabalho no projeto._

# MediClaw — React Panel

> Next.js 16 frontend for the MediClaw AI health assistant.
> Provides a landing page, authenticated chat interface with SSE streaming, and an admin panel. Health data is captured automatically from conversational messages — no manual log forms.

## Stack

| Tool                     | Version         | Role                                |
| ------------------------ | --------------- | ----------------------------------- |
| Next.js                  | 16 (App Router) | Framework                           |
| React                    | 19              | UI library                          |
| TypeScript               | 5               | Type safety                         |
| Chakra UI                | v3              | Component library                   |
| Axios                    | latest          | HTTP client (with JWT interceptors) |
| Vitest + Testing Library | latest          | Automated tests                     |
| Husky + Prettier         | latest          | Pre-commit formatting               |

---

## Implementation status

| Epic            | Feature                                                         | Status      | Tests |
| --------------- | --------------------------------------------------------------- | ----------- | ----- |
| 1 — Foundation  | Providers, layout, HTTP client, SSE wrapper                     | ✅ Complete | 5     |
| 2 — Auth        | Login, register, landing page, route protection, logout         | ✅ Complete | 12    |
| 3 — Health Logs | _Descontinuado pelo pivot — dados capturados via chat_          | ❌ Removed  | —     |
| 4 — Chat com IA | Conversation list, streaming SSE, bubbles, citations, disclaimer | ✅ Complete | 16    |
| 5 — Profile     | _Descontinuado pelo pivot — perfil preenchido via chat_         | ❌ Removed  | —     |
| 6 — Admin       | Knowledge base upload, metrics dashboard                        | ✅ Complete | —     |

**40 automated tests passing** across Epics 1, 2, 4. Run with `npm test`.

---

## Route map

| Route                | Description                                                    | Auth     |
| -------------------- | -------------------------------------------------------------- | -------- |
| `/`                  | Landing page with hero, feature cards, CTA; redirects to `/chat` if authenticated | Public   |
| `/login`             | Email + password login                                         | Public   |
| `/register`          | Registration with client-side validation                       | Public   |
| `/chat`              | Conversation list with pagination                              | Required |
| `/chat/[id]`         | Chat with history + SSE streaming                              | Required |
| `/admin/knowledge`   | Knowledge base upload (file picker), document table + delete   | Admin    |
| `/admin/metrics`     | Platform metrics dashboard (6 stat cards)                      | Admin    |

Admin routes require `user.role === "ADMIN"`. No dashboard, health, or profile routes exist — health data is collected conversationally.

---

## Quick start

### Option 1 — Without devcontainer (fastest)

**1. Configure environment**

```bash
cp .env.local.example .env.local
```

Or create `.env.local` manually:

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

**2. Install and run**

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

> The Django API must be running on port 8000 for authenticated flows.
> Layout, providers, and the auth UI render without a live backend.

---

### Option 2 — Devcontainer (VS Code / Cursor)

This project ships a Dev Container configuration that connects to the shared `mediclaw-dev-network` Docker network alongside `django-api`.

**Host requirements:**

- Docker Desktop (or Docker Engine + Compose v2)
- VS Code or Cursor with the Dev Containers extension

**Steps:**

1. Create the shared Docker network (once per machine):

```bash
docker network create mediclaw-dev-network
```

2. Open this folder in VS Code/Cursor.
3. Run **Dev Containers: Reopen in Container**.
4. Wait for `postCreateCommand` to finish (`npm ci`).

**Start the dev server inside the container:**

```bash
npm run dev -- --hostname 0.0.0.0 --port 3000
```

**Network hostnames inside the container:**

| Service       | Hostname       |
| ------------- | -------------- |
| This frontend | `react-painel` |
| Django API    | `django-api`   |

---

## Running tests

```bash
npm test
```

All 40 tests run with Vitest + jsdom. No live backend needed — all external dependencies are mocked.

```bash
npm run build        # TypeScript check + production build (must pass with 0 errors)
npm run lint         # ESLint
npm run format       # Prettier — rewrite staged files
npm run format:check # Prettier — check only (used by CI/pre-commit)
```

---

## What's ready — file reference

### Epic 1 — Foundation

| Layer         | File                                  | Description                                                                                                     |
| ------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Types         | `src/types/api.ts`                    | `ApiResponse<T>`, `User`, `Conversation`, `Message`, `AdminMetrics`, `KnowledgeDocument`                        |
| HTTP client   | `src/lib/api.ts`                      | Axios instance; request interceptor injects `Authorization: Bearer`; response interceptor auto-refreshes on 401 |
| Auth helpers  | `src/lib/auth.ts`                     | `login()`, `logout()`, `refreshToken()` — simplejwt-compatible                                                  |
| SSE wrapper   | `src/lib/sse.ts`                      | `openStream(url, { onToken, onCitation, onDone, onError }) → cleanup`                                           |
| Chat utils    | `src/lib/chat-disclaimer.ts`          | `hasEducationalDisclaimer(text): boolean` — deduplicates disclaimer footers in `MessageBubble`                  |
| Auth context  | `src/context/AuthContext.tsx`         | Hydrates user from `localStorage` on mount; exposes `login`, `logout`, `setUser`, `isLoading`                   |
| Toast context | `src/context/ToastContext.tsx`        | `showToast(message, status)` via Chakra UI v3 `createToaster`                                                   |
| Providers     | `src/components/providers.tsx`        | `ChakraProvider → AuthProvider → ToastProvider`                                                                 |
| Layout        | `src/components/layout/PageShell.tsx` | Fixed sidebar (desktop) + `DrawerRoot` (mobile)                                                                 |
| Layout        | `src/components/layout/Sidebar.tsx`   | Single nav link "Chat IA"; brand "MediClaw / Assistente de saúde"                                               |
| Layout        | `src/components/layout/TopBar.tsx`    | Username display + logout button                                                                                 |

### Epic 2 — Auth

| Layer       | File                                        | Description                                                                          |
| ----------- | ------------------------------------------- | ------------------------------------------------------------------------------------ |
| Landing     | `src/app/page.tsx`                          | Public landing page; hero section, 3 feature cards, CTA buttons; redirects authenticated users to `/chat` |
| Auth layout | `src/app/(auth)/layout.tsx`                 | Centered layout without sidebar (route group `(auth)`)                               |
| Pages       | `src/app/(auth)/login/page.tsx`             | Renders `LoginForm`                                                                  |
| Pages       | `src/app/(auth)/register/page.tsx`          | Renders `RegisterForm`                                                               |
| Spinner     | `src/components/common/FullPageSpinner.tsx` | Full-viewport centered spinner for loading/redirect states                           |
| Auth forms  | `src/components/auth/LoginForm.tsx`         | Email + password; inline error for `INVALID_CREDENTIALS`; loading button state       |
| Auth forms  | `src/components/auth/RegisterForm.tsx`      | name/email/password/confirm/terms; client-side validation; email duplicate detection |
| Guard       | `src/components/auth/RequireAuth.tsx`       | Redirects to `/login` if not authenticated                                           |
| Guard       | `src/components/auth/RequireAdmin.tsx`      | Redirects to `/chat` if `role !== "ADMIN"`                                           |
| App layout  | `src/app/(app)/layout.tsx`                  | Route group `(app)` wrapped in `RequireAuth`                                         |

### ~~Epic 3 — Health Logs~~ _(Descontinuado pelo pivot de 2026-05-27)_

Os formulários de logs de saúde (`/dashboard`, `/health/*`) foram removidos. Dados biométricos agora são capturados automaticamente via parsing de mensagens de chat no backend (`capture_from_message`).

### ~~Epic 5 — Perfil~~ _(Descontinuado pelo pivot de 2026-05-27)_

A página `/profile` foi removida. O perfil do usuário (nome, altura, sexo, data de nascimento) é coletado durante o onboarding conversacional (conversa de boas-vindas gerada pelo backend no cadastro).

### Epic 4 — Chat com IA

| Layer     | File                                    | Description                                                                                                                           |
| --------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Hook      | `src/hooks/useConversations.ts`         | Paginated list, create, delete; `pageRef` tracks page cursor; uses DRF `next` field for `hasMore`                                     |
| Hook      | `src/hooks/useMessages.ts`              | `GET /api/v1/conversations/{id}/` → `{ conversation, messages }`                                                                      |
| Component | `src/components/chat/CitationBadge.tsx` | Blue badge with source name from `message.metadata.citations`                                                                         |
| Component | `src/components/chat/MessageBubble.tsx` | User/assistant alignment; disclaimer deduplication via `hasEducationalDisclaimer`; guardrail badge; markdown rendering; citation list  |
| Component | `src/components/chat/ChatInput.tsx`     | Textarea + SSE via `openStream`; optimistic user bubble; partial assistant bubble; `cleanupRef` prevents EventSource leaks on unmount |
| Page      | `src/app/(app)/chat/page.tsx`           | Conversation list; "+ Nova" button; relative timestamps; delete confirmation; "Carregar mais"                                         |
| Page      | `src/app/(app)/chat/[id]/page.tsx`      | Message history + `ChatInput`; auto-scroll; uses `use(params)` for Next.js 16 dynamic routes                                          |
| CSS       | `src/app/globals.css`                   | `.typing-cursor::after` + `@keyframes blink` for streaming cursor animation                                                           |

### Epic 6 — Admin

| Layer | File                                           | Description                                                                            |
| ----- | ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| Hook  | `src/hooks/useAdminKnowledge.ts`               | Upload, list, delete knowledge documents; wraps `/api/v1/admin/knowledge/upload`       |
| Hook  | `src/hooks/useAdminMetrics.ts`                 | `GET /api/v1/admin/metrics` → `AdminMetrics`                                           |
| Page  | `src/app/(app)/admin/knowledge/page.tsx`       | File picker upload (PDF/TXT/MD), document table with status badge, delete confirmation |
| Page  | `src/app/(app)/admin/metrics/page.tsx`         | 6 stat cards: users, conversations, messages today, tokens today, blocks today, KB docs |

### Known limitations

- Audit logs (`/api/v1/admin/logs`) not implemented
- Knowledge document polling for `PROCESSING` status not implemented

### Automated tests

| File                                                   | Tests | What's covered                                                                                                                               |
| ------------------------------------------------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/__tests__/context/AuthContext.test.tsx`           | 5     | Hydration: no token, valid token, expired+refresh ok, expired+refresh fail, `login` stores tokens                                            |
| `src/__tests__/components/layout/PageShell.test.tsx`   | 5     | Children, brand, logout button, "Chat IA" nav link, username in topbar                                                                       |
| `src/__tests__/components/auth/LoginForm.test.tsx`     | 4     | Fields rendered, `INVALID_CREDENTIALS` inline error, toast on other errors, redirect on success                                              |
| `src/__tests__/components/auth/RegisterForm.test.tsx`  | 8     | 5 client-side validations + no API call on error + email duplicate + redirect on success                                                     |
| `src/__tests__/lib/chat-disclaimer.test.ts`            | 2     | `hasEducationalDisclaimer` detects disclaimer in body; returns false when absent                                                             |
| `src/__tests__/components/chat/MessageBubble.test.tsx` | 8     | Content, markdown rendering, disclaimer deduplication, no disclaimer for USER, guardrail badge, no badge when not blocked, citations         |
| `src/__tests__/components/chat/ChatInput.test.tsx`     | 8     | Renders, disabled when empty, calls openStream, optimistic bubble, disabled during stream, done callback, error toast, token accumulation    |

---

## Manual verification checklists

### Auth (Epic 2)

| Check                     | How                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| Landing page              | Open `http://localhost:3000` — landing page renders with hero, cards and CTA buttons                  |
| Landing redirect          | Open `http://localhost:3000` with valid token — redirected to `/chat`                                 |
| Login success             | Submit valid credentials → redirected to `/chat`; tokens stored in `localStorage`                     |
| Login invalid credentials | Submit wrong credentials → inline error "E-mail ou senha inválidos" (not a toast)                     |
| Register success          | Submit valid form → redirected to `/chat`; user hydrated in `AuthContext`                             |
| Register duplicate email  | Submit form with existing email → inline error "Este e-mail já está cadastrado"                       |
| Register validation       | Try weak password, mismatched passwords, unchecked terms → field-level error messages                 |
| Route protection          | Open `/chat` with no token → redirected to `/login`                                                   |
| Hydration on refresh      | Add valid `access_token` + `refresh_token` to `localStorage`, open `/chat`, refresh page → stays     |
| Logout                    | Click "Sair" in `TopBar` → tokens cleared, redirected to `/login`                                     |

### Chat com IA (Epic 4)

| Check                        | How                                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------ |
| Conversation list            | Open `/chat` authenticated — list renders with timestamps; empty state shows "Nenhuma conversa ainda"  |
| New conversation             | Click "+ Nova" → POST creates conversation → redirected to `/chat/{id}`                                |
| Load more                    | If > 1 page of conversations exists, "Carregar mais" appears and loads next page                       |
| Delete conversation          | Click 🗑 → confirmation modal; confirm → conversation removed from list                                |
| Message history              | Open `/chat/{id}` with prior messages → history renders with user (right) / assistant (left) alignment |
| Streaming tokens             | Send a message with live API → tokens appear progressively; cursor `                                   | ` blinks while streaming |
| Optimistic user bubble       | User message appears immediately before the API responds                                               |
| Disclaimer                   | Every assistant bubble shows "ℹ Esta orientação é educativa e não substitui um profissional de saúde." |
| Guardrail badge              | `blocked_by_guardrail=true` → red "Resposta limitada" badge above the bubble                           |
| Citation badge               | `citation` SSE event fires → blue "📚 Source" badge below the assistant bubble                         |
| Input disabled during stream | Textarea and "Enviar" button are disabled while SSE stream is open                                     |
| SSE cleanup on navigate      | Navigate away mid-stream → no EventSource leak (check Network tab in DevTools)                         |
| SSE error toast              | Disconnect API mid-stream → toast "Conexão interrompida"; input re-enables without page refresh        |

### Foundation (Epic 1)

| Check                         | How                                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| Providers mount without error | Open `http://localhost:3000` — no console errors                                        |
| `AuthContext` hydration       | DevTools → Application → Local Storage; add a valid `access_token` and refresh the page |
| Toast                         | Call `showToast("test", "success")` via React DevTools                                  |
| Sidebar (desktop)             | Resize browser to ≥ 768 px — fixed sidebar with "Chat IA" link appears on the left      |
| Sidebar (mobile)              | Resize browser to < 768 px — hamburger button appears; tap to open drawer               |
| Admin routes                  | Log in as `ADMIN` — `/admin/knowledge` and `/admin/metrics` accessible                  |
| TypeScript                    | `npm run build` — must complete with 0 type errors                                      |
| Lint                          | `npm run lint` — no warnings                                                            |

---

## Husky + Prettier (pre-commit)

This repository uses Husky to run lint-staged on every commit. The hook is **non-blocking** (`npx lint-staged || true`) so a formatting error never prevents a commit.

**First-time setup (inside devcontainer or after `npm install`):**

```bash
npm run prepare
```

**Manual commands:**

```bash
npm run lint           # ESLint only
npm run format         # Prettier — rewrite files
npm run format:check   # Prettier — check only
```

---

## Troubleshooting

| Problem                                      | Fix                                                                                                |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Container fails — network not found | `docker network create mediclaw-dev-network`                                      |
| Dependencies fail to install        | `rm -rf node_modules package-lock.json && npm install`                            |
| SSE not streaming                   | Check `NEXT_PUBLIC_API_URL` in `.env.local` and confirm the Django API is running |

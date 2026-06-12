# Evolução Frontend — MediClaw Painel

Registro das tarefas concluídas por épico, em ordem de execução.

---

## Epic 1 — Foundation (2026-05-21)

### Story 1.1 — Providers e layout root

- Configurado `ChakraProvider` com `defaultSystem` em `src/components/providers.tsx`
- Criado `src/context/AuthContext.tsx` com interface `{ user, isAuthenticated, isLoading, login, logout }`
  - Hidrata o usuário a partir do `localStorage` no mount via `GET /api/v1/auth/me`
  - Tenta refresh automático se o token estiver expirado; limpa storage se falhar
- Criado `src/context/ToastContext.tsx` com `showToast(message, status)`
  - Usa `createToaster` do Chakra UI v3 (a API `useToast` foi removida na v3)
  - Renderiza `<Toaster>` com template de toast customizado (indicador de tipo + título + fechar)
- Ambos os contexts integrados ao layout root via `src/components/providers.tsx`
- Build TypeScript sem erros (`npm run build`)

### Story 1.2 — Cliente HTTP com interceptors JWT

- Criado `src/types/api.ts` com as interfaces:
  `ApiResponse<T>`, `User`, `Conversation`, `Citation`, `Message`, `HealthSummary`, `KnowledgeDocument`
- Criado `src/lib/auth.ts` com funções:
  - `login(email, password)` — chama `POST /api/v1/auth/login`
  - `refreshToken()` — chama `POST /api/v1/auth/refresh` (simplejwt) e atualiza `localStorage`
  - `logout()` — limpa `localStorage` e redireciona para `/login`
- Atualizado `src/lib/api.ts` com:
  - Request interceptor: injeta `Authorization: Bearer <token>` de `localStorage`
  - Response interceptor: captura 401, tenta refresh e reenvia; faz logout se refresh falhar
  - Guard de SSR: `typeof window !== "undefined"` antes de acessar `localStorage`

### Story 1.3 — Layout global com navegação

- Criado `src/components/layout/Sidebar.tsx`
  - Links de navegação com destaque de rota ativa via `usePathname()`
  - Seção "Admin" renderizada condicionalmente para `user.role === "ADMIN"`
  - Links estilizados com `chakra(Link)` (Next.js + Chakra v3 — `Box as={Link}` gera erro de tipo)
- Criado `src/components/layout/TopBar.tsx`
  - Exibe nome do usuário e botão "Sair" (chama `logout()` do `AuthContext`)
  - Botão de menu hamburger para abrir drawer em mobile
- Criado `src/components/layout/PageShell.tsx`
  - Desktop (≥ md): sidebar fixa à esquerda com `position: fixed` e `marginLeft` no main
  - Mobile (< md): sidebar em `DrawerRoot` do Chakra v3 controlado por `useState`

### Story 1.4 — Wrapper SSE

- Criado `src/lib/sse.ts` com `openStream(url, { onToken, onCitation, onDone, onError }) → cleanup`
  - Despacha callbacks por tipo de evento: `token`, `citation`, `done`, `error`
  - Fecha `EventSource` automaticamente nos eventos `done` e `error`
  - Retorna função de cleanup que fecha o `EventSource` ao ser chamada

---

---

## Epic 2 — Auth (2026-05-21)

### Story 2.1 — Tela de login (`/login`)

- Criado `src/components/auth/LoginForm.tsx`
  - Campos `email` e `password` com `FieldRoot/FieldLabel/Input` do Chakra v3
  - Submit chama `login()` de `lib/auth.ts` e chama `authLogin(tokens, user)` do `AuthContext`
  - Erro `INVALID_CREDENTIALS` exibido inline abaixo do campo senha (não como toast)
  - Qualquer outro erro → toast via `useToast()`
  - Botão com prop `loading={isLoading}` (Chakra v3 Button tem suporte nativo)
  - Link para `/register` usando `chakra(Link)` (padrão necessário para compat. TypeScript Next.js + Chakra v3)
- Criado `src/app/(auth)/login/page.tsx` — renderiza `LoginForm`

### Story 2.2 — Tela de cadastro (`/register`)

- Criado `src/components/auth/RegisterForm.tsx`
  - Campos: `name`, `email`, `password`, `confirm_password`, `accept_terms`
  - Validação client-side antes do submit: tamanho mínimo do nome, força da senha, confirmação de senha, checkbox obrigatório
  - Checkbox usa `CheckboxRoot/CheckboxHiddenInput/CheckboxControl/CheckboxIndicator/CheckboxLabel` do Chakra v3
  - `onCheckedChange={(e) => setAcceptTerms(e.checked === true)}` — API do Ark UI subjacente
  - Detecção de e-mail duplicado: verifica `code === "EMAIL_ALREADY_EXISTS"` OU `message.includes("já cadastrado")` — backend retorna código `UNHANDLED` para erros de validação do DRF
  - Sucesso segue o mesmo fluxo do login
- Criado `src/app/(auth)/register/page.tsx` — renderiza `RegisterForm`

### Story 2.3 — Proteção de rotas e layout de auth

- Criado `src/app/(auth)/layout.tsx`
  - Layout centralizado (`Flex minH="100dvh" align="center" justify="center"`) sem sidebar
  - Route group `(auth)` evita que o layout root com `PageShell` seja aplicado nas páginas de auth
- Criado `src/components/common/FullPageSpinner.tsx`
  - Spinner centralizado na viewport; usado durante hydration do `AuthContext` e redirect
- Criado `src/app/dashboard/page.tsx` (placeholder para Epic 3)
  - Guard: `useEffect` verificando `!isLoading && !isAuthenticated` → `router.replace("/login")`
  - Exibe `FullPageSpinner` enquanto `isLoading || !isAuthenticated`
  - Envolve conteúdo em `PageShell` após autenticado
- Atualizado `src/app/page.tsx`
  - Redireciona para `/dashboard` ou `/login` baseado em `isAuthenticated` após `isLoading=false`

### Story 2.4 — Logout

- `TopBar` já chama `logout()` do `AuthContext` (implementado no Epic 1)
- `logout()` em `lib/auth.ts` limpa `localStorage` e redireciona via `window.location.href`

### Correções e atualizações

- Atualizado `src/types/api.ts`: renomeado `name` → `first_name`; adicionado `accepted_terms_at: string | null`
- Atualizado `src/lib/auth.ts`: `login()` agora retorna `{ access, refresh, user: User }` (API retorna o objeto user)
- Atualizado `src/components/layout/TopBar.tsx`: `user.name` → `user.first_name`

---

## Epic 3 — Health Logs (2026-05-23)

### O que foi desenvolvido

- **Hooks de API**:
  - `src/hooks/useHealthSummary.ts`: Busca o resumo de 7 dias ou de um período configurável para a dashboard.
  - `src/hooks/useHealthLogs.ts`: Hook genérico e reutilizável (`fetchLogs`, `addLog`, `deleteLog`) que simplifica a comunicação das 4 telas de saúde.
- **Tipagens em `src/types/api.ts`**: Adicionadas interfaces `WeightLog`, `SleepLog`, `ActivityLog` e `NutritionNote`.
- **Componentes de UI**:
  - `SummaryCard` (`src/components/health/SummaryCard.tsx`): Cartão usado no Dashboard para demonstrar resumos rápidos com skeleton loading.
  - `DeleteConfirmModal` (`src/components/common/DeleteConfirmModal.tsx`): Modal padronizado para confirmar ações perigosas antes de enviar requisições de exclusão.
- **Páginas Adicionadas/Atualizadas**:
  - **Dashboard (`/dashboard`)**: Atualizado com os cartões de resumo da saúde.
  - **Peso (`/health/weight`)**: Tela com formulário (validando 20 a 400kg e data não futura) e tabela do histórico de peso.
  - **Sono (`/health/sleep`)**: Formulário com slider e tabela onde a nota da qualidade do sono é exibida num badge colorido (verde, amarelo ou vermelho).
  - **Atividades Físicas (`/health/activity`)**: Adicionado controle de tipo (Select) e duração de exercício.
  - **Nutrição (`/health/nutrition`)**: Campo textarea flexível para acompanhamento das refeições, com contador visual de caracteres limitando a 1000.

---

---

## ~~Epic 5 — Perfil~~ — DESCONTINUADO (2026-05-27)

- Removida pelo pivot da aplicação. Dados do usuário (nome, altura, sexo biológico, data de nascimento) coletados durante o onboarding conversacional via `ensure_welcome_conversation`.

---

## Epic 6 — Painel Admin (2026-05-27)

- Criado `src/hooks/useAdminKnowledge.ts`: `uploadDocument`, `listDocuments`, `deleteDocument`
- Criado `src/hooks/useAdminMetrics.ts`: busca `GET /api/v1/admin/metrics`
- Criado `src/components/admin/KnowledgeTable.tsx`: tabela com badges de status (`PROCESSING` / `INDEXED` / `ERROR`), delete com `AlertDialog`, delete bloqueado enquanto `PROCESSING`
- Criado `src/components/admin/MetricsCard.tsx`: grid 3×2 com 6 cartões de métricas
- Upload via `<input type="file">` (drag-and-drop descontinuado); validação client-side de tipo e tamanho (10 MB) antes de chamar a API
- Proteção de rotas via `RequireAdmin` — redireciona para `/chat` se `user.role !== "ADMIN"`
- **Pendente:** polling de status para documentos `PROCESSING`; tabela de logs de auditoria (aguarda endpoint `/api/v1/admin/logs` no backend); testes automatizados do módulo admin

---

## Epic 4 — Chat com IA (2026-05-31)

### Story 4.1 — Lista de conversas (`/chat`)

- Criado `src/hooks/useConversations.ts`: `list` (paginado), `create`, `deleteConversation`
- Página `/chat` lista conversas ordenadas por `updated_at desc`, botão "Nova conversa" → `POST /api/v1/conversations` → redirect para `/chat/{id}`, delete com `AlertDialog` de confirmação

### Story 4.2 — Histórico de mensagens

- Criado `src/hooks/useMessages.ts`: `GET /api/v1/conversations/{id}` retorna `{ conversation, messages }`
- Criado `src/components/chat/MessageBubble.tsx`: bolha do usuário (direita, cor primária) e do assistente (esquerda, cor neutra); disclaimer fixo abaixo de cada bolha do assistente; badge "Resposta limitada" quando `blocked_by_guardrail=true`; lista de `CitationBadge` a partir de `message.metadata.citations`
- Scroll automático para a última mensagem ao carregar histórico e a cada token recebido

### Story 4.3 — Streaming SSE

- Criado `src/components/chat/ChatInput.tsx`: estado `isStreaming`, `partialReply`, `citations`; abre SSE via `openStream()` ao submeter; acumula tokens progressivamente; cursor piscante (CSS `@keyframes blink`) durante streaming; input desabilitado durante streaming; cleanup via `cleanupRef` ao desmontar
- Criado `src/components/chat/CitationBadge.tsx`: badge discreto com nome da fonte
- Criado `src/lib/chat-disclaimer.ts`: `hasEducationalDisclaimer(text): boolean` — evita duplicar disclaimer quando o backend já inclui na resposta

---

## Pendente

### Epic 6 (Admin) — itens em aberto

- Polling de status de documentos `PROCESSING` (Story 6.2)
- Tabela de logs de auditoria (aguarda endpoint `/api/v1/admin/logs` no backend)
- Testes automatizados do módulo admin

---

## Epic 7 — Patient Management (2026-05-31)

- `Patient`, `PatientDetail`, `ConversationSummary` em `src/types/api.ts`; `Conversation` atualizado com `patient: { id, first_name } | null`; `User.profile` removido
- `src/lib/sse.ts`: `onDone` estendido com `patient_id`, `patient_first_name`, `patient_created`
- `src/hooks/usePatients.ts`: `usePatients()` e `usePatient(id)` — dependências estáveis (`[]`, `[id]`) para evitar loop por `showToast` instável
- `src/hooks/useConversations.ts`: `updateConversationPatient` adicionado
- `Sidebar.tsx`: link "Pacientes" + seção Admin; usa `useAuth()` para controle de role
- `chat/page.tsx`: exibe `conv.patient?.first_name` como título
- `ChatInput.tsx`: prop `onPatientIdentified` para callback SSE `done`
- `chat/[id]/page.tsx`: `patientName` atualizado em tempo real via SSE
- Componentes: `PatientTable`, `PatientHeader`, `PatientConversations`, `PatientHealthTabs`
- Rotas `/patients` e `/patients/[id]` com detalhe, tabs de saúde e exclusão
- **Fix backend necessário:** `PatientListSerializer` precisou de anotações (`Count`, `Max`, `Subquery`) para retornar `conversation_count`, `last_seen_at`, `latest_weight_kg`

---

## Pendente

### Epic 6 (Admin) — itens em aberto

- Polling de status de documentos `PROCESSING` (Story 6.2)
- Tabela de logs de auditoria (aguarda endpoint `/api/v1/admin/logs` no backend)
- Testes automatizados do módulo admin

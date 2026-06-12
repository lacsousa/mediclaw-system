# MediClaw — Tasks Frontend (Roadmap Executável)

> Versão: 1.0 | Data: 2026-05-14
> Documento principal de execução. Marque `- [x]` ao concluir.
> Referência: [PRD.md](PRD.md) | [ARCHITECTURE.md](ARCHITECTURE.md)
> **Regra:** finalizar (com testes visuais no browser) o épico antes de iniciar o próximo.

---

## Mapeamento Épicos → Arquivos

| Épico            | Arquivo                                                    |
| ---------------- | ---------------------------------------------------------- |
| E1 — Foundation  | [epics/epic-1-foundation.md](epics/epic-1-foundation.md)   |
| E2 — Auth        | [epics/epic-2-auth.md](epics/epic-2-auth.md)               |
| E3 — Health Logs | [epics/epic-3-health-logs.md](epics/epic-3-health-logs.md) |
| E4 — Chat com IA | [epics/epic-4-chat.md](epics/epic-4-chat.md)               |
| E5 — Perfil      | [epics/epic-5-profile.md](epics/epic-5-profile.md)         |
| E6 — Admin       | [epics/epic-6-admin.md](epics/epic-6-admin.md)             |

---

## Epic 1 — Foundation

> Pré-requisito de todos os demais. Bloqueante.

### Story 1.1 — Providers e layout root

- [x] `ChakraProvider` configurado em `app/layout.tsx`
- [x] `AuthContext` criado em `context/AuthContext.tsx` com `{ user, isAuthenticated, isLoading, login, logout }`
- [x] `ToastContext` criado em `context/ToastContext.tsx`
- [x] Ambos os contexts envolvendo a aplicação no layout root
- [x] TypeScript strict sem erros em `npm run build`

### Story 1.2 — Cliente HTTP com interceptors JWT

- [x] `lib/api.ts` exporta instância Axios com `baseURL = process.env.NEXT_PUBLIC_API_URL`
- [x] Request interceptor injeta `Authorization: Bearer <token>`
- [x] Response interceptor captura 401, tenta refresh, reenvia ou faz logout
- [x] `lib/auth.ts` com funções `login()`, `logout()`, `refreshToken()`
- [x] `types/api.ts` com `ApiResponse<T>`, `User`, `Conversation`, `Message`, `HealthSummary`, `KnowledgeDocument`

### Story 1.3 — Layout global com navegação

- [x] `components/layout/PageShell.tsx` com sidebar e topbar
- [x] `components/layout/Sidebar.tsx` com links de navegação e destaque de rota ativa
- [x] `components/layout/TopBar.tsx` com nome do usuário e logout
- [x] Sidebar responsiva: drawer em mobile (breakpoint `md`)
- [x] Links de admin visíveis apenas para `role === "ADMIN"`

### Story 1.4 — Wrapper SSE

- [x] `lib/sse.ts::openStream(url, { onToken, onCitation, onDone, onError }) → cleanup`
- [x] Fecha `EventSource` automaticamente ao chamar cleanup

### Story 1.5 — Testes Automatizados

- [x] Testar renderização do `PageShell` e proteção de rotas
- [x] Garantir que o `AuthContext` hidrata o usuário corretamente

---

## Epic 2 — Auth

### Story 2.1 — Tela de login

- [x] `/login` com formulário `email` + `password`
- [x] Submit chama `POST /api/v1/auth/login`
- [x] Tokens salvos em `localStorage`, `AuthContext` atualizado
- [x] Redirect para `/dashboard` após sucesso
- [x] Erros mapeados para mensagens em português
- [x] Loading state no botão

### Story 2.2 — Tela de cadastro

- [x] `/register` com campos `name`, `email`, `password`, `confirm_password`, `accept_terms`
- [x] Validação client-side antes do submit
- [x] Submit chama `POST /api/v1/auth/register`
- [x] Mesmo fluxo de sucesso do login

### Story 2.3 — Proteção de rotas

- [x] Páginas privadas verificam `isAuthenticated` e redirecionam para `/login`
- [x] Páginas admin verificam `user.role === "ADMIN"` e redirecionam para `/chat`
- [x] `/` é landing page pública; redireciona para `/chat` se autenticado

### Story 2.4 — Logout

- [x] Botão na topbar chama `logout()` → limpa `localStorage` → redirect `/login`

### Story 2.5 — Testes Automatizados

- [x] Testar validação de formulários de Login/Register
- [x] Mock de respostas de sucesso/erro da API

---

## ~~Epic 3 — Health Logs~~ _(Descontinuado — pivot de 2026-05-27)_

> **Motivo:** Os formulários de entrada manual de dados biométricos (`/dashboard`, `/health/*`) foram removidos da interface. O backend agora extrai dados de saúde automaticamente via NLP das mensagens de chat (`capture_from_message`). Usuários fornecem informações conversacionalmente durante o onboarding e nas interações diárias com o assistente.

- ~~Story 3.1 — Dashboard com summary~~ (removido)
- ~~Story 3.2 — Peso~~ (removido)
- ~~Story 3.3 — Sono~~ (removido)
- ~~Story 3.4 — Atividade Física~~ (removido)
- ~~Story 3.5 — Nutrição~~ (removido)
- ~~Story 3.6 — Testes Automatizados~~ (removido)

---

## Epic 4 — Chat com IA

### Story 4.1 — Lista de conversas

- [x] `hooks/useConversations.ts` com list, create, delete
- [x] `/chat` listando conversas com paginação
- [x] Botão "Nova conversa" criando e redirecionando

### Story 4.2 — Interface de chat

- [x] `hooks/useMessages.ts` carregando histórico da conversa
- [x] `components/chat/MessageBubble.tsx` diferenciando usuário e assistente
- [x] Disclaimer fixo abaixo de cada bolha de assistente
- [x] Scroll automático para a última mensagem

### Story 4.3 — Streaming SSE

- [x] `components/chat/ChatInput.tsx` abrindo SSE ao submeter
- [x] Tokens acumulados progressivamente com cursor animado
- [x] `CitationBadge` exibido ao receber evento `citation`
- [x] Badge "Resposta limitada" quando `blocked=true`
- [x] Input desabilitado durante streaming
- [x] Cleanup do EventSource ao desmontar componente ou ao navegar

### Story 4.4 — Testes Automatizados

- [x] Renderização correta das mensagens no chat
- [x] Testar tratamento do evento de streaming no UI

---

## ~~Epic 5 — Perfil~~ _(Descontinuado — pivot de 2026-05-27)_

> **Motivo:** A página `/profile` foi removida. O perfil do usuário (nome, altura, sexo biológico, data de nascimento) é coletado durante o onboarding conversacional. O backend gera automaticamente uma conversa de boas-vindas no cadastro (`ensure_welcome_conversation`) que solicita esses dados em linguagem natural.

- ~~Story 5.1 — Visualizar e editar perfil~~ (removido)
- ~~Story 5.2 — Exclusão de conta~~ (removido)
- ~~Story 5.3 — Testes Automatizados~~ (removido)

---

## Epic 6 — Admin

### Story 6.1 — Upload de documentos

- [x] `/admin/knowledge` com file picker (input type=file — drag-and-drop descontinuado)
- [x] `POST /api/v1/admin/knowledge/upload` com feedback de erro (`FILE_TOO_LARGE`, `INVALID_FILE_TYPE`)
- [x] Suporte a PDF, TXT e MD

### Story 6.2 — Tabela de documentos

- [x] Tabela listando documentos com badge de status (PROCESSING / INDEXED / ERROR)
- [x] Delete com confirmação
- [ ] Polling de status a cada 3s para documentos `PROCESSING` (pendente)

### Story 6.3 — Métricas

- [x] `/admin/metrics` com 6 cartões: usuários, conversas, mensagens hoje, tokens hoje, bloqueios hoje, docs indexados
- [ ] Tabela de logs de auditoria (pendente — endpoint não implementado no backend)

### Story 6.4 — Testes Automatizados

- [ ] Testes automatizados do módulo admin (pendente)

---

## Epic 7 — Patient Management

> **Pivot arquitetural:** Exibe a entidade `Patient` na interface — sidebar, lista de pacientes e detalhe.
> Referência: [epics/epic-7-patient.md](epics/epic-7-patient.md)
> **Pré-requisito:** Backend Epic 8 completo.

### Story 7.1 — Tipos e hooks

- [x] `Patient`, `PatientDetail`, `ConversationSummary` adicionados a `src/types/api.ts`
- [x] `Conversation` type atualizado com `patient: { id: number; first_name: string } | null`
- [x] `User.profile` removido (migrado para Patient no backend)
- [x] `src/hooks/usePatients.ts` — `usePatients()` (lista paginada) e `usePatient(id)` com deps estáveis
- [x] `src/lib/sse.ts` — `onDone` estendido com `patient_id`, `patient_first_name`, `patient_created`
- [x] `useConversations.ts` — `updateConversationPatient` adicionado

### Story 7.2 — Sidebar com nome do paciente

- [x] `chat/page.tsx` exibe `conv.patient?.first_name` como título principal da conversa
- [x] Exibe título ou "Nova conversa" quando `patient === null`
- [x] `ChatInput.tsx` — prop `onPatientIdentified` chama callback ao receber `patient_id` no SSE `done`
- [x] `chat/[id]/page.tsx` — estado local `patientName` atualiza heading em tempo real via SSE

### Story 7.3 — Página `/patients`

- [x] `app/(app)/patients/page.tsx` criada
- [x] `components/patients/PatientTable.tsx` com colunas: Nome, Último atend., Consultas, Peso atual, IMC
- [x] Skeleton loading durante `isLoading`
- [x] Paginação via "Carregar mais"
- [x] IMC calculado client-side (`weight / (height/100)²`)

### Story 7.4 — Página `/patients/[id]`

- [x] `app/(app)/patients/[id]/page.tsx` criada
- [x] `components/patients/PatientHeader.tsx` — nome, DOB, sexo, altura, IMC com categoria
- [x] `components/patients/PatientConversations.tsx` — lista de consultas com link `→ /chat/{id}`
- [x] `components/patients/PatientHealthTabs.tsx` — tabs read-only: Peso / Sono / Atividade / Nutrição
- [x] Delete de paciente com `DeleteConfirmModal` → redirect `/patients`

### Story 7.5 — Navegação

- [x] Link "Pacientes" (🧑‍⚕️) adicionado na sidebar abaixo de "Chat IA"
- [x] Sidebar usa `useAuth()` para exibir seção Admin apenas para `role=ADMIN`
- [x] Rotas `/patients` e `/patients/[id]` no grupo `(app)` (RequireAuth)

---

## Definition of Done (Frontend MVP)

- [x] Todas as user stories `Must` do PRD funcionando no browser
- [x] Streaming SSE exibindo tokens progressivamente no chat
- [x] Rotas privadas redirecionam corretamente sem token
- [x] TypeScript: `npm run build` sem erros
- [ ] ESLint: `npm run lint` sem warnings (não verificado)
- [ ] Testado em Chrome, Firefox e Safari (mobile)
- [x] Disclaimer médico visível em todas as respostas do assistente

---

_Para cada épico, abra o arquivo correspondente em `epics/` para detalhes de componentes e exemplos._

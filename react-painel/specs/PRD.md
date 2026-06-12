# MediClaw — Product Requirements Document (Frontend)

> **Versão:** 1.0 | **Data:** 2026-05-14 | **Status:** Rascunho
> **Referência:** [MVP.md](MVP.md) | **Próximo:** [ARCHITECTURE.md](ARCHITECTURE.md) → [TASKS.md](TASKS.md)
> **Escopo:** Frontend (Next.js + Chakra UI). Backend Django é API externa.

---

## Objetivo do Produto

Construir um painel web em Next.js que sirva como interface para a plataforma MediClaw: permite ao usuário registrar dados biométricos, conversar com a IA de saúde preventiva e, para administradores, gerenciar a base de conhecimento e monitorar métricas.

**Restrição central:** O painel **NÃO** implementa lógica de IA, guardrails ou processamento de dados de saúde. Toda lógica de negócio reside no backend.

---

## Personas

### P1 — Usuário Final (Marina, 38 anos)

- Pratica atividade física regular e quer acompanhar sua evolução
- Registra peso, sono e refeições semanalmente via celular e desktop
- Quer conversar com a IA sobre seus dados de forma simples e confiável
- Conhecimento técnico: básico/médio

### P2 — Administrador

- Gestor da plataforma; faz upload de documentos científicos
- Monitora uso, qualidade da IA e eventuais abusos
- Conhecimento técnico: intermediário

---

## Requisitos Não-Funcionais

### RNF-01 — Performance

- First Contentful Paint (FCP) < 1,5s em conexão 4G
- Transições de página < 300ms (rotas Next.js pré-renderizadas)
- Streaming SSE inicia exibição do primeiro token em < 2s

### RNF-02 — Acessibilidade

- Nível AA do WCAG 2.1 para componentes Chakra
- Contraste mínimo 4.5:1 para texto normal
- Navegação completa por teclado em formulários e chat

### RNF-03 — Segurança

- Sem secrets em variáveis `NEXT_PUBLIC_*`
- Nenhum conteúdo do usuário em `dangerouslySetInnerHTML`
- Tokens JWT não logados no console em produção
- Rotas privadas protegidas no cliente (redirect) e, futuramente, no middleware Next.js

### RNF-04 — Responsividade

- Layout funcional em mobile (≥ 375px), tablet (≥ 768px) e desktop (≥ 1280px)
- Componentes Chakra respondem ao breakpoint automaticamente

### RNF-05 — Manutenibilidade

- TypeScript strict mode em todos os arquivos
- Nenhum `any` implícito
- Componentes com menos de 200 linhas; lógica em hooks separados

---

## Épicos e User Stories

---

### EPIC-01 — Foundation

**Objetivo:** Estrutura base do projeto com providers, roteamento, cliente HTTP e layout global.

#### US-01 — Providers e layout root

**Como** desenvolvedor,
**Quero** ter o `layout.tsx` root configurado com ChakraProvider e AuthContext,
**Para que** todos os componentes acessem tema e estado de autenticação.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E1](epics/epic-1-foundation.md)

**Critérios de Aceite:**

- [ ] `ChakraProvider` envolve a aplicação com tema base
- [ ] `AuthContext` disponível em toda a árvore
- [ ] `ToastContext` para notificações globais
- [ ] `npm run dev` sobe sem erros de TypeScript

---

#### US-02 — Cliente HTTP com interceptors JWT

**Como** desenvolvedor,
**Quero** uma instância Axios configurada com `baseURL` e interceptors de token,
**Para que** nenhuma tela precise gerenciar autenticação manualmente.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E1](epics/epic-1-foundation.md)

**Critérios de Aceite:**

- [ ] `@/lib/api.ts` exporta instância Axios com `baseURL = NEXT_PUBLIC_API_URL`
- [ ] Request interceptor injeta `Authorization: Bearer <token>` automaticamente
- [ ] Response interceptor captura 401, tenta refresh via `POST /auth/refresh`, reenvia original
- [ ] Se refresh falha → limpa localStorage e redireciona para `/login`
- [ ] Tipos TypeScript para o envelope `{ data, error, meta }`

---

#### US-03 — Layout global com navegação

**Como** usuário autenticado,
**Quero** uma sidebar/topbar consistente em todas as páginas privadas,
**Para que** eu navegue sem perder contexto.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E1](epics/epic-1-foundation.md)

**Critérios de Aceite:**

- [ ] `components/layout/PageShell.tsx` envolve páginas privadas com sidebar e topbar
- [ ] Sidebar lista: Chat IA; e Administração para role ADMIN
- [ ] Topbar exibe nome do usuário e botão de logout
- [ ] Layout responsivo: sidebar colapsa em drawer em mobile
- [ ] Rota ativa destacada visualmente

---

### EPIC-02 — Auth

**Objetivo:** Login, cadastro, proteção de rotas e renovação automática de token.

#### US-04 — Tela de login

**Como** visitante,
**Quero** fazer login com e-mail e senha,
**Para que** eu acesse o painel.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**

- [ ] Formulário com campos `email` e `password` e botão "Entrar"
- [ ] `POST /api/v1/auth/login` → armazena tokens em `localStorage`
- [ ] Erros mapeados: `INVALID_CREDENTIALS` → "E-mail ou senha inválidos"
- [ ] Redirect para `/dashboard` após sucesso
- [ ] Loading state no botão durante a requisição

---

#### US-05 — Tela de cadastro

**Como** visitante,
**Quero** criar conta com nome, e-mail, senha e aceite dos termos,
**Para que** eu use a plataforma.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**

- [ ] Campos: `name`, `email`, `password`, `confirm_password`, checkbox `accept_terms`
- [ ] Validação client-side: senha ≥ 8 chars, confirmação igual, aceite obrigatório
- [ ] `POST /api/v1/auth/register` → armazena tokens e redireciona para `/dashboard`
- [ ] Erros: `EMAIL_ALREADY_EXISTS` → "Este e-mail já está cadastrado"
- [ ] Checkbox de termos com link para o documento (placeholder no MVP)

---

#### US-06 — Proteção de rotas e AuthContext

**Como** sistema,
**Quero** que rotas privadas redirecionem para `/login` se não autenticado,
**Para que** dados sensíveis não sejam expostos.

**Prioridade:** Must | **Esforço:** S | **Epic:** [E2](epics/epic-2-auth.md)

**Critérios de Aceite:**

- [ ] `AuthContext` expõe `{ user, isAuthenticated, isLoading, login, logout }`
- [ ] Páginas privadas verificam `isAuthenticated` e redirecionam se falso
- [ ] Rotas admin verificam `user.role === "ADMIN"` e redirecionam para `/dashboard` se insuficiente
- [ ] Logout limpa `localStorage` e redireciona para `/login`

---

### ~~EPIC-03 — Dashboard e Logs de Saúde~~ — DESCONTINUADO

> **Status:** Descontinuado em 2026-05-27 pelo pivot da aplicação.
> **Motivo:** Os formulários de entrada manual de dados biométricos foram removidos. O backend extrai dados de saúde automaticamente via NLP das mensagens de chat (`capture_from_message`). Rotas `/dashboard` e `/health/*` não existem mais. Ver [epic-3-health-logs.md](epics/epic-3-health-logs.md).

~~**Objetivo:** Dashboard de resumo e CRUD de todos os tipos de log biométrico.~~

~~US-07 — Dashboard com summary~~ (removida)

~~US-08 — Registro e listagem de peso~~ (removida)

~~US-09 — Registro e listagem de sono~~ (removida)

~~US-10 — Registro e listagem de atividade física~~ (removida)

~~US-11 — Registro e listagem de nutrição~~ (removida)

---

### EPIC-04 — Chat com IA

**Objetivo:** Interface de conversas com streaming SSE e exibição de guardrails e citações.

#### US-12 — Lista de conversas

**Como** usuário,
**Quero** ver minhas conversas com a IA e criar novas,
**Para que** eu organize meu histórico.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E4](epics/epic-4-chat.md)

**Critérios de Aceite:**

- [ ] `GET /api/v1/conversations` lista conversas ordenadas por `updated_at desc`
- [ ] Cada item: título (ou "Sem título"), data da última mensagem
- [ ] Botão "Nova conversa" → `POST /api/v1/conversations` → redirect para `/chat/{id}`
- [ ] Paginação (scroll infinito ou botão "Carregar mais")
- [ ] `DELETE /api/v1/conversations/{id}` com confirmação

---

#### US-13 — Interface de chat com streaming

**Como** usuário,
**Quero** enviar mensagens e ver a resposta da IA aparecer em tempo real,
**Para que** a experiência seja fluida.

**Prioridade:** Must | **Esforço:** L | **Epic:** [E4](epics/epic-4-chat.md)

**Critérios de Aceite:**

- [ ] Histórico de mensagens carregado via `GET /api/v1/conversations/{id}`
- [ ] Bolhas de mensagem diferenciadas: usuário (direita, cor primária) e assistente (esquerda, neutro)
- [ ] Submit do formulário abre SSE em `/api/v1/conversations/{id}/stream?prompt=...&token=<jwt>`
- [ ] Tokens acumulados progressivamente na bolha do assistente (animação de cursor)
- [ ] Evento `citation` exibe badge/link de fonte abaixo da bolha
- [ ] Evento `done` com `blocked=true` exibe badge "Resposta limitada" e ícone de aviso
- [ ] Disclaimer exibido abaixo de toda resposta do assistente
- [ ] Erro SSE exibe toast e não trava o input
- [ ] Input desabilitado enquanto resposta está sendo recebida

---

### ~~EPIC-05 — Perfil~~ — DESCONTINUADO

> **Status:** Descontinuado em 2026-05-27 pelo pivot da aplicação.
> **Motivo:** A página `/profile` foi removida. Nome, altura, sexo biológico e data de nascimento são coletados durante o onboarding conversacional (`ensure_welcome_conversation`). Ver [epic-5-profile.md](epics/epic-5-profile.md).

~~US-14 — Visualizar e editar perfil~~ (removida)

---

### EPIC-06 — Painel Admin

**Objetivo:** Gestão da base de conhecimento e visualização de métricas.

#### US-15 — Upload e gestão de documentos

**Como** administrador,
**Quero** fazer upload de documentos e acompanhar a indexação,
**Para que** a IA tenha embasamento científico atualizado.

**Prioridade:** Must | **Esforço:** M | **Epic:** [E6](epics/epic-6-admin.md)

**Critérios de Aceite:**

- [ ] Zona de drag-and-drop que aceita PDF, MD, TXT (máx 10MB)
- [ ] `POST /api/v1/admin/knowledge/upload` com progress bar
- [ ] Erros: `FILE_TOO_LARGE` → "Arquivo excede 10MB"; `INVALID_FILE_TYPE` → "Tipo não suportado"
- [ ] Tabela de documentos: título, status (badge colorido), chunks indexados, data
- [ ] Polling de `GET /api/v1/admin/knowledge/{id}/status` a cada 3s enquanto `PROCESSING`
- [ ] `DELETE /api/v1/admin/knowledge/{id}` com confirmação

---

#### US-16 — Métricas e logs de auditoria

**Como** administrador,
**Quero** ver métricas de uso e logs de atividade,
**Para que** eu monitore a plataforma.

**Prioridade:** Should | **Esforço:** S | **Epic:** [E6](epics/epic-6-admin.md)

**Critérios de Aceite:**

- [ ] `GET /api/v1/admin/metrics` exibe cartões: usuários, conversas, mensagens hoje, tokens hoje, bloqueios hoje
- [ ] `GET /api/v1/admin/logs` exibe tabela paginada com `action`, `user`, `created_at`
- [ ] Filtros por `action` e período

---

## Fora do Escopo (MVP)

| Item                                 | Motivo                                                |
| ------------------------------------ | ----------------------------------------------------- |
| Formulários manuais de logs de saúde | Substituídos por extração conversacional (pivot)      |
| Página de perfil (`/profile`)        | Dados coletados via onboarding conversacional (pivot) |
| Gráficos de evolução temporal        | Fase 2                                                |
| Dark mode                            | Fase 2                                                |
| PWA / notificações push              | Fase 2                                                |
| Internacionalização                  | Fase 3                                                |
| Testes E2E com Playwright            | Fase 2                                                |
| Autenticação Social (Google/GitHub)  | Aguarda backend                                       |

---

## Critérios de Aceite do MVP (Definition of Done)

- [ ] Usuário consegue cadastrar, logar e conversar com a IA
- [ ] Streaming SSE exibe tokens progressivamente no chat
- [ ] Disclaimer médico visível em toda resposta do assistente
- [ ] Respostas bloqueadas pelo guardrail exibem indicação visual clara
- [ ] Admin faz upload de documento e acompanha indexação
- [ ] Todas as rotas privadas redirecionam corretamente sem token
- [ ] TypeScript sem erros de compilação
- [ ] Layout funcional em mobile, tablet e desktop

---

_Próximo documento: [ARCHITECTURE.md](ARCHITECTURE.md)_

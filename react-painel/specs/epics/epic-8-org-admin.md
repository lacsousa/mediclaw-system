# Epic 8 — Administração de Organização (Pós-MVP)

> **Objetivo:** Interface para o admin de uma organização (clínica/empresa cliente) gerenciar quais usuários pertencem à conta e qual base de conhecimento (RAG) cada um acessa.
> **Pré-requisito:** E6 (Admin) completo. Backend Epic 9 deployado.
> **Referência:** [Backend epic-9-rag-multi-tenant.md](../../../django-api/specs/epics/epic-9-rag-multi-tenant.md)
> **Status:** Planejado, não iniciado. Fora do escopo do PRD v1.0 (MVP acadêmico) — desenho para a fase de venda B2B.

---

## Contexto

Hoje `/admin/metrics` e `/conhecimento` já existem (Epic 6) mas são de escopo **global**: `IsAdminRole` enxerga tudo, e a base de conhecimento é compartilhada por todos os usuários autenticados. Quando o backend implementar o Epic 9 (RAG segmentado por conta), o frontend precisa de uma tela nova para que o admin de uma organização — não necessariamente um admin global do sistema — gerencie sua própria equipe e sua própria base de conhecimento, sem ver nem afetar outras organizações clientes.

## Novos tipos TypeScript

```typescript
// src/types/api.ts — adições

export interface Organization {
  id: number;
  name: string;
  member_count: number;
  created_at: string;
}

export interface OrganizationMember {
  id: number;
  user_id: number;
  email: string;
  name: string;
  role: "MEMBER" | "ORG_ADMIN";
  joined_at: string;
}

// KnowledgeDocument — atualizado (escopo do dono)
export interface KnowledgeDocument {
  id: number;
  title: string;
  status: "PROCESSING" | "INDEXED" | "ERROR";
  chunk_count: number | null;
  created_at: string;
  owner_scope: "USER" | "ORGANIZATION"; // novo campo
  owner_label: string; // nome do usuário ou da organização, para exibição
}
```

---

## Story 8.1 — Hook `useOrganization` e permissão `RequireOrgAdmin`

### `hooks/useOrganization.ts`

```typescript
export function useOrganizationMembers(orgId: number) {
  // GET    /api/v1/organizations/{orgId}/members
  // POST   /api/v1/organizations/{orgId}/members
  // DELETE /api/v1/organizations/{orgId}/members/{userId}
}
```

### `components/auth/RequireOrgAdmin.tsx`

Segue o padrão de `RequireAdmin` já existente (Epic 6): redireciona para `/chat` se o usuário autenticado não tiver `role === "ORG_ADMIN"` na organização corrente (campo novo em `useAuth()`, populado a partir de `GET /api/v1/auth/me`).

### Critérios

- [ ] `useOrganizationMembers(orgId)` retorna lista de membros, `addMember`, `removeMember`
- [ ] `RequireOrgAdmin` bloqueia acesso e redireciona não-admins de organização
- [ ] `Organization` e `OrganizationMember` exportados de `src/types/api.ts`

---

## Story 8.2 — Página de equipe (`/admin/organizacao`)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Minha Organização — Clínica Vida Plena                        │
├────────────────────────────────────────────────────────────────┤
│  Membros (4)                                    [+ Convidar]   │
├────────────────────────────────────────────────────────────────┤
│  Nome            │ E-mail              │ Papel      │ Ações    │
├────────────────────────────────────────────────────────────────┤
│  Dra. Ana Costa  │ ana@vidaplena.com   │ Admin      │  —       │
│  Dr. Bruno Lima  │ bruno@vidaplena.com │ Membro     │ [Remover]│
└────────────────────────────────────────────────────────────────┘
```

### `components/admin/OrgMemberTable.tsx`

- Colunas: Nome | E-mail | Papel | Ações
- "Remover" desabilitado para o próprio usuário logado (não pode se autoexcluir)
- Convite de novo membro via modal simples (e-mail + papel), reaproveita padrão de formulário do cadastro admin (`POST /api/v1/admin/users`, já existente no Epic 2 backend)

### Critérios

- [ ] `/admin/organizacao` acessível apenas via `RequireOrgAdmin`
- [ ] Tabela lista membros com papel (Admin/Membro)
- [ ] Convite de novo membro funcional, com validação de e-mail
- [ ] Remoção de membro com confirmação (`DeleteConfirmModal`, já existente)

---

## Story 8.3 — `/conhecimento` exibe escopo do documento

### Ajuste em `components/admin/KnowledgeTable.tsx` (Epic 6)

Nova coluna **Escopo**, mostrando se o documento pertence ao usuário individual ou à organização (`owner_scope` / `owner_label`). Upload passa a ter um seletor "Indexar para: [ Só eu | Minha organização ]" quando o usuário pertence a uma organização.

### Critérios

- [ ] Coluna "Escopo" exibe "Pessoal" ou nome da organização
- [ ] Seletor de escopo no upload aparece apenas para usuários com organização
- [ ] Usuário sem organização mantém comportamento atual (sempre "Pessoal"), sem quebra de UI

---

## Story 8.4 — Navegação

### Sidebar (`components/layout/Sidebar.tsx`) — atualização

```
Chat IA
Pacientes
Conhecimento
— Administração —      (ADMIN ou ORG_ADMIN)
  Documentos
  Métricas             (apenas ADMIN global)
  Organização           ← novo (apenas ORG_ADMIN)
```

### Critérios

- [ ] Link "Organização" visível somente para `ORG_ADMIN`
- [ ] "Métricas" continua restrito a admin global (`IsAdminRole`), não a `ORG_ADMIN`

---

## Critérios de Aceite da Epic

- [ ] `/admin/organizacao` lista, convida e remove membros da própria organização
- [ ] Admin de uma organização não enxerga nem afeta membros de outra organização
- [ ] `/conhecimento` mostra escopo (pessoal vs. organização) e permite escolher o escopo no upload
- [ ] Sidebar exibe "Organização" apenas para `ORG_ADMIN`
- [ ] TypeScript sem erros (`npm run build`)

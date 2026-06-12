# Epic 7 — Patient Management (Frontend)

> **Objetivo:** Expor a entidade `Patient` na interface: sidebar mostra nome do paciente, nova página `/patients` lista todos os pacientes do médico, `/patients/[id]` mostra histórico e dados de saúde do paciente.
> **Pré-requisito:** E4 (Chat com IA) completo. Backend Epic 8 deployado.
> **Referência:** [Backend epic-8-patient.md](../../../django-api/specs/epics/epic-8-patient.md)

---

## Novos tipos TypeScript

```typescript
// src/types/api.ts — adições

export interface Patient {
  id: number;
  first_name: string;
  birth_date: string | null; // ISO 8601
  biological_sex: "M" | "F" | "OTHER" | null;
  height_cm: number | null;
  conversation_count: number;
  last_seen_at: string | null; // ISO 8601
  latest_weight_kg: number | null;
}

export interface PatientDetail extends Patient {
  weight_logs: WeightLog[];
  sleep_logs: SleepLog[];
  activity_logs: ActivityLog[];
  nutrition_notes: NutritionNote[];
  conversations: ConversationSummary[];
}

// Conversation — atualizado (patient agora incluído)
export interface Conversation {
  id: number;
  title: string;
  patient: { id: number; first_name: string } | null; // novo campo
  created_at: string;
  updated_at: string;
}
```

---

## Story 7.1 — Hook `usePatients` e tipos

### `hooks/usePatients.ts`

```typescript
export function usePatients() {
  // GET /api/v1/patients/  (paginado)
  // retorna { patients, isLoading, error, loadMore }
}

export function usePatient(id: number) {
  // GET /api/v1/patients/{id}/
  // retorna { patient: PatientDetail | null, isLoading, error }
}
```

### Critérios

- [ ] `usePatients()` retorna lista paginada com `loadMore()`
- [ ] `usePatient(id)` retorna detalhe com logs e conversas
- [ ] `Patient` e `PatientDetail` exportados de `src/types/api.ts`
- [ ] `Conversation` type atualizado com campo `patient`

---

## Story 7.2 — Sidebar com nome do paciente

### Comportamento

A sidebar (lista de conversas em `/chat`) mostra o nome do paciente assim que ele é identificado no chat.

```
┌────────────────────────────────────┐
│  Chat IA            [+ Nova]       │
├────────────────────────────────────┤
│  João Silva         há 5 min   [🗑]│  ← patient.first_name
│  Maria Oliveira     há 2h      [🗑]│
│  Nova conversa      há 1d      [🗑]│  ← patient = null
└────────────────────────────────────┘
```

### `components/chat/ConversationItem.tsx`

Props: `conversation: Conversation`

- Se `conversation.patient !== null` → exibe `patient.first_name` como título principal
- Se `conversation.patient === null` → exibe "Nova conversa" (ou `conversation.title` se preenchido)
- Timestamp relativo da última mensagem

### Atualização via evento SSE `done`

Quando o evento `done` inclui `patient_id` (novo campo do backend):

- Atualiza o item da conversa na lista com `patient: { id, first_name }` recebido
- Sem necessidade de re-fetch da lista inteira

```typescript
// Em ChatInput.tsx — no callback onDone:
onDone: (data) => {
  if (data.patient_id && data.patient_first_name) {
    updateConversationPatient(conversationId, {
      id: data.patient_id,
      first_name: data.patient_first_name,
    });
  }
  setIsStreaming(false);
  fetchMessages();
};
```

### Critérios

- [ ] `ConversationItem` exibe `patient.first_name` quando disponível
- [ ] Exibe "Nova conversa" quando `patient === null`
- [ ] Evento SSE `done` com `patient_id` atualiza o item da conversa na sidebar sem reload

---

## Story 7.3 — Página de lista de pacientes (`/patients`)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Meus Pacientes                                                │
├────────────────────────────────────────────────────────────────┤
│  Nome           │ Último atend. │ Consultas │ Peso │  IMC     │
├────────────────────────────────────────────────────────────────┤
│  João Silva     │ hoje, 14:30   │     3     │ 80kg │ 24,7     │
│  Maria Oliveira │ ontem         │     1     │ 65kg │ 22,1     │
│  [sem dados]    │ 3 dias atrás  │     1     │  —   │  —       │
│                 ...                                            │
│                      [Carregar mais]                           │
└────────────────────────────────────────────────────────────────┘
```

### `components/patients/PatientTable.tsx`

Colunas:

- **Nome** — link para `/patients/{id}`
- **Último atendimento** — `last_seen_at` formatado como relativo
- **Consultas** — `conversation_count`
- **Peso atual** — `latest_weight_kg` ou "—"
- **IMC** — calculado a partir de `latest_weight_kg` + `height_cm` (se ambos disponíveis), caso contrário "—"

### `hooks/usePatients.ts`

Paginação via botão "Carregar mais" (`?page=N`).

### Critérios

- [ ] Rota `/patients` acessível para usuário autenticado
- [ ] Tabela carrega com skeleton durante `isLoading`
- [ ] Valores `null` exibidos como "—" sem crash
- [ ] IMC calculado client-side quando peso e altura disponíveis
- [ ] Link de cada linha leva para `/patients/{id}`
- [ ] Paginação via "Carregar mais"

---

## Story 7.4 — Página de detalhe do paciente (`/patients/[id]`)

### Layout

```
┌───────────────────────────────────────────────────────────┐
│  ← Pacientes   João Silva                                 │
│  Nascimento: 15/03/1985 · Sexo: Masculino · Altura: 178cm │
│  Peso atual: 80 kg · IMC: 25,2 (Sobrepeso)               │
├───────────────────────────────────────────────────────────┤
│  CONSULTAS (3)                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 30/05/2026  Nova consulta                   [Abrir] │  │
│  │ 15/05/2026  Consulta de acompanhamento      [Abrir] │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  HISTÓRICO DE SAÚDE                                       │
│  [Peso]  [Sono]  [Atividade]  [Nutrição]   ← tabs        │
│                                                           │
│  [Tabela do tipo selecionado...]                          │
├───────────────────────────────────────────────────────────┤
│  [Excluir paciente]  (vermelho, abre modal de confirmação)│
└───────────────────────────────────────────────────────────┘
```

### Componentes

- `components/patients/PatientHeader.tsx` — Nome, dados de perfil, IMC
- `components/patients/PatientConversations.tsx` — Lista de conversas com link `→ /chat/{id}`
- `components/patients/PatientHealthTabs.tsx` — Tabs: Peso / Sono / Atividade / Nutrição com tabelas read-only

### Delete de paciente

- Botão "Excluir paciente" → `DeleteConfirmModal` (reutiliza `components/common/DeleteConfirmModal.tsx`)
- Ao confirmar → `DELETE /api/v1/patients/{id}/`
- Sucesso → redirect para `/patients` + toast "Paciente removido"

### Critérios

- [ ] Header exibe nome, DOB formatada, sexo, altura, IMC calculado
- [ ] Lista de conversas com link para `/chat/{id}`
- [ ] Tabs de saúde exibem dados read-only do paciente
- [ ] "Excluir paciente" com confirmação → redireciona para `/patients`
- [ ] 404 se `id` não pertencer ao médico autenticado (tratado como "not found")

---

## Story 7.5 — Navegação e rotas

### Novas rotas

| Rota             | Componente                         | Auth    |
| ---------------- | ---------------------------------- | ------- |
| `/patients`      | `app/(app)/patients/page.tsx`      | Privado |
| `/patients/[id]` | `app/(app)/patients/[id]/page.tsx` | Privado |

### Sidebar (`components/layout/Sidebar.tsx`) — atualização

Adicionar link "Pacientes" na sidebar abaixo de "Chat IA":

```
Chat IA
Pacientes          ← novo
— Administração —  (apenas ADMIN)
  Documentos
  Métricas
```

---

## Critérios de Aceite da Epic

- [ ] `Conversation` type inclui `patient: { id, first_name } | null`
- [ ] Sidebar exibe nome do paciente em cada conversa (quando disponível)
- [ ] Evento SSE `done` com `patient_id` atualiza a conversa na sidebar em tempo real
- [ ] `/patients` lista pacientes com nome, último atendimento, nº de consultas, peso atual, IMC
- [ ] `/patients/[id]` exibe perfil completo + conversas + tabs de saúde
- [ ] Delete de paciente com confirmação funciona e redireciona para `/patients`
- [ ] Link "Pacientes" na sidebar navegável
- [ ] TypeScript sem erros (`npm run build`)

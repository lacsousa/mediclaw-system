# Epic 6 — Painel Admin ✅ Completo

> **Objetivo:** Gestão da base de conhecimento (RAG) e visualização de métricas de uso.
> **Pré-requisito:** Épicos 1 e 2.
> **Status:** Implementado (2026-05-27). Upload usa file picker (input type=file), não drag-and-drop. Polling de status pendente.
>
> **Atualização (2026-05-31):** A base de conhecimento deixou de ser admin-only. A tela saiu de `/admin/knowledge` para **`/conhecimento`** (sem `RequireAdmin`) e virou item de navegação principal **"Conhecimento"** (📚), abaixo de "Pacientes", visível para qualquer usuário autenticado. Apenas **Métricas** (`/admin/metrics`) continua admin-only. O backend relaxou a permissão dos endpoints de knowledge de `IsAdminRole` para `IsAuthenticated`.

---

## Story 6.1 — Upload de documentos (`/conhecimento`)

### `hooks/useKnowledge.ts`

```typescript
export function useKnowledge() {
  // GET    /api/v1/admin/knowledge
  // POST   /api/v1/admin/knowledge/upload (FormData)
  // GET    /api/v1/admin/knowledge/{id}/status
  // DELETE /api/v1/admin/knowledge/{id}
}
```

### `components/admin/UploadZone.tsx`

- Drag-and-drop com `onDrop`; também aceita clique para file picker
- Tipos aceitos: `application/pdf`, `text/markdown`, `text/plain`
- Tamanho máximo: 10MB (validado client-side antes do upload)
- Progress bar durante o upload (`onUploadProgress` do Axios)
- Mensagens de erro:
  - Arquivo > 10MB → "Arquivo excede o limite de 10MB"
  - Tipo inválido → "Tipo não suportado. Use PDF, MD ou TXT"
  - `FILE_TOO_LARGE` do backend → mesmo texto
  - `INVALID_FILE_TYPE` do backend → mesmo texto

### `components/admin/KnowledgeTable.tsx`

Colunas: Título | Status | Chunks | Data de upload | Ações

**Status badges:**

- `PROCESSING` → amarelo + spinner
- `INDEXED` → verde
- `ERROR` → vermelho + tooltip com `error_message`

**Polling de status:**

```typescript
useEffect(() => {
  const processingDocs = documents.filter((d) => d.status === "PROCESSING");
  if (processingDocs.length === 0) return;

  const interval = setInterval(async () => {
    for (const doc of processingDocs) {
      const status = await fetchStatus(doc.id);
      updateDocument(doc.id, status);
    }
  }, 3000);

  return () => clearInterval(interval);
}, [documents]);
```

**Delete:**

- Bloqueado (botão desabilitado + tooltip "Aguarde a indexação") se `status === "PROCESSING"`
- Confirmação via `AlertDialog` antes do DELETE

---

## Story 6.2 — Métricas e logs (`/admin/metrics`)

### `components/admin/MetricsCard.tsx`

`GET /api/v1/admin/metrics` retorna:

```json
{
  "users_total": 42,
  "conversations_total": 187,
  "messages_today": 34,
  "tokens_today": 28400,
  "guardrail_blocks_today": 3,
  "kb_documents_indexed": 12
}
```

Layout em grid 3×2 de cartões numerados.

### Tabela de logs

`GET /api/v1/admin/logs` com filtros:

- `action` — select com as ações disponíveis
- `from` / `to` — filtro de período

Colunas: Ação | Usuário | Data/hora

---

## Story 6.4 — Testes Automatizados

### O que fazer

- Testar se o componente `KnowledgeTable` trata o status `PROCESSING` de maneira que bloqueie ações como exclusão.
- Testar a validação do formato de arquivo no componente `UploadZone` antes de chamar o backend.

---

## Critérios de Aceite da Epic

- [x] `/conhecimento` acessível a qualquer usuário autenticado (sem `RequireAdmin`); item "Conhecimento" 📚 na nav principal, abaixo de "Pacientes"
- [x] Página `/admin/metrics` redireciona para `/chat` se `user.role !== "ADMIN"` (via `RequireAdmin`)
- [x] Upload via file picker (input type=file) — não drag-and-drop
- [x] Arquivo > 10MB e tipo inválido retornam erro do backend com mensagem clara
- [x] Documento aparece na tabela após upload bem-sucedido
- [ ] Polling de status de "PROCESSING" para "INDEXED"/"ERROR" (pendente)
- [x] Delete com confirmação remove o documento da tabela
- [x] Cartões de métricas exibem valores do backend (6 cartões)
- [ ] Tabela de logs de auditoria (pendente — endpoint `/api/v1/admin/logs` não implementado)

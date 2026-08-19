# RAG / Delete, Tarefas de Implementação

> Sequência executável para reimplementar a exclusão a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `KnowledgeDocument`
- [ ] `get_collection` singleton (ver collection-singleton)

## Tarefas

- [ ] **T-01**, View `delete_document` com 404, 409 e remoção no vector store
  - Origem no legado: `apps/rag/views.py:117-131`
  - Critério de pronto: inexistente → 404; `PROCESSING` → 409; senão `coll.delete(where={"document_id": str(doc.id)})` + `doc.delete()` → 204
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Delete de documento INDEXED → 204 e chunks removidos do ChromaDB
- [ ] **TT-02**, Delete de documento inexistente → 404
- [ ] **TT-03**, Delete durante PROCESSING → 409
- [ ] **TT-04**, Sem token → 401

## Ordem Sugerida

1. T-01.
2. Testes TT-01 a TT-04 (mockar ChromaDB).

## Lacunas Pendentes (🔴)

- [ ] Escopar acesso ao `uploaded_by` (hoje qualquer autenticado deleta documentos de terceiros).

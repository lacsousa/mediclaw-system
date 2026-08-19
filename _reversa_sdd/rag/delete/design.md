# RAG / Delete, Design Técnico

> Contrato operacional de **COMO** a exclusão é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| DELETE | `/api/v1/admin/knowledge/<doc_id>/` | `doc_id: int` | `204` | 204, 404 (`NOT_FOUND`), 409 (`CONFLICT`) |

## Fluxo Principal

1. Busca `KnowledgeDocument` por `pk`; inexistente → `AppError("NOT_FOUND", ..., 404)`. (`views.py:117-125`) 🟢
2. `status == "PROCESSING"` → `AppError("CONFLICT", ..., 409)` — documenta "aguarde concluir". (`views.py:123-125`) 🟢
3. `coll = get_collection()`; `coll.delete(where={"document_id": str(doc.id)})` → remove chunks. (`views.py:127-128`) 🟢
4. `doc.delete()` → remove registro. (`views.py:129`) 🟢
5. `record("KB_DELETE", user, metadata={document_id})` — stub; retorna 204. (`views.py:130-131`) 🟢

## Fluxos Alternativos

- **[Documento inexistente]:** 404 `NOT_FOUND`. 🟢
- **[Delete durante PROCESSING]:** 409 `CONFLICT`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.rag.services.vector_store.get_collection` | Vector store | `coll.delete(where=...)` |
| `apps.common.exceptions.AppError` | Erros padronizados | `NOT_FOUND`, `CONFLICT` |
| `apps.audit.services.log.record` | Auditoria (stub) | `KB_DELETE` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Delete do vector store por `where document_id` (IDs estruturados) | `views.py:128`; `ingestion.py:48` | 🟢 |
| Recusa exclusão durante PROCESSING | `views.py:123-125` | 🟢 |
| Busca sem escopo ao `uploaded_by` | `views.py:119-125` | 🟢 |

## Riscos e Lacunas

- 🔴 **Acesso cruzado entre usuários:** qualquer autenticado pode deletar documentos de terceiros (`views.py:119-123` sem filtro de `uploaded_by`).
- 🟢 Auditoria de `KB_DELETE` é stub (nada persiste — ADR 007).

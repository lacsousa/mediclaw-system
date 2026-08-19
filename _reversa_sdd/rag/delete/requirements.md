# RAG / Delete — Requisitos

> Contrato operacional do caso de uso **Exclusão de documento** (`DELETE /api/v1/admin/knowledge/<doc_id>/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Remove um documento da base: apaga os chunks do ChromaDB (por `where document_id`) e o `KnowledgeDocument` do banco. Recusa exclusão durante a ingestão (`PROCESSING`). Registra `KB_DELETE` (stub).

## Regras de Negócio

- **RN-01** — Documento inexistente → 404 `NOT_FOUND`. 🟢
- **RN-02** — `status == "PROCESSING"` → 409 `CONFLICT` ("aguarde concluir a indexação"). 🟢
- **RN-03** — `coll.delete(where={"document_id": str(doc.id)})` remove os chunks. 🟢
- **RN-04** — `doc.delete()` remove o registro; `record("KB_DELETE", ...)` (stub). 🟢
- **RN-05** — Busca por `pk` **sem escopo ao `uploaded_by`** — qualquer autenticado deleta qualquer documento. 🟢 (lacuna de segurança)

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Excluir documento | Must | DELETE `/api/v1/admin/knowledge/<doc_id>/` → 204 |
| RF-02 | Tratar documento inexistente | Must | `pk` ausente → 404 `NOT_FOUND` |
| RF-03 | Bloquear exclusão em PROCESSING | Must | `status == "PROCESSING"` → 409 `CONFLICT` |
| RF-04 | Remover do vector store | Must | `coll.delete(where={"document_id": str(doc.id)})` antes do `doc.delete()` |

## Critérios de Aceitação

```gherkin
Dado um documento INDEXED ou ERROR
Quando faço DELETE em /api/v1/admin/knowledge/<doc_id>/
Então recebo 204, os chunks são removidos do ChromaDB e o documento do banco

Dado um documento inexistente
Quando faço DELETE em /api/v1/admin/knowledge/<doc_id>/
Então recebo 404 NOT_FOUND

Dado um documento em PROCESSING
Quando faço DELETE em /api/v1/admin/knowledge/<doc_id>/
Então recebo 409 CONFLICT
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/rag/views.py:117-131` | `delete_document` | 🟢 |
| `apps/rag/services/vector_store.py` | `get_collection` → `coll.delete` | 🟢 |
| `apps/rag/models.py` | `KnowledgeDocument` | 🟢 |
| `apps/audit/services/log.py` | `record("KB_DELETE")` — stub | 🟢 |

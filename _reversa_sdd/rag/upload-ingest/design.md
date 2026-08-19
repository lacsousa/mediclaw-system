# RAG / Upload & Ingest, Design Técnico

> Contrato operacional de **COMO** o upload/ingestão é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| POST | `/api/v1/admin/knowledge/upload/` | multipart `file` + `title` opcional | `{id, title, status, chunk_count}` | 201, 400 (`VALIDATION_ERROR`/`FILE_TOO_LARGE`/`INVALID_FILE_TYPE`) |

## Fluxo Principal

1. Valida presença de `file` no multipart; ausente → `VALIDATION_ERROR` 400. (`views.py:27-29`) 🟢
2. Valida `f.size <= MAX_BYTES` (10MB); acima → `FILE_TOO_LARGE` 400. (`views.py:30-31`) 🟢
3. Valida `f.content_type ∈ ALLOWED_MIMETYPES`; fora → `INVALID_FILE_TYPE` 400. (`views.py:32-35`) 🟢
4. `title = (request.data.get("title") or f.name)[:200]`; cria `KnowledgeDocument(status="PROCESSING", uploaded_by=request.user)`. (`views.py:37-44`) 🟢
5. `ingest(doc, f.read())` — **síncrono**. (`views.py:45`) 🟢
   - `_extract_text`: PDF → junta `page.extract_text()`; MD/TXT → `decode("utf-8", errors="replace")`. Vazio → `ValueError`. (`ingestion.py:20-42`) 🟢
   - `_split`: `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`. (`ingestion.py:27-29`) 🟢
   - `_get_embeddings()`: `OpenAIEmbeddings(model=env EMBEDDING_MODEL, default text-embedding-3-small)` — **nova instância por ingestão**. (`ingestion.py:32-35`) 🟢
   - `coll.add(ids=["{doc_id}-{i}-{uuid8}"], documents=chunks, embeddings=vectors, metadatas=[{document_id, title, chunk_index}])`. (`ingestion.py:47-57`) 🟢
   - Sucesso → `status="INDEXED"`, `chunk_count=len(chunks)`. Falha → log `document_index_failed`, `status="ERROR"`, `error_message=str(e)[:1000]`. (`ingestion.py:59-70`) 🟢
6. `record("KB_UPLOAD", user=request.user, metadata={document_id, status})` — stub. (`views.py:46-50`) 🟢
7. Retorna 201 `{id, title, status, chunk_count}`. (`views.py:51-59`) 🟢

## Fluxos Alternativos

- **[Arquivo ausente]:** `AppError("VALIDATION_ERROR", "Arquivo ausente.", 400)`. 🟢
- **[Arquivo > 10MB]:** `AppError("FILE_TOO_LARGE", ..., 400)`. 🟢
- **[MIME não permitido]:** `AppError("INVALID_FILE_TYPE", ..., 400)` com o tipo na mensagem. 🟢
- **[Documento sem texto extraível]:** `ValueError("Documento vazio ou sem texto extraível.")` → `status=ERROR`. 🟢
- **[Falha em qualquer etapa]:** `except Exception` → `logger.exception("document_index_failed")`, `status=ERROR`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| ChromaDB `PersistentClient` | Vector store | `get_collection().add(...)` |
| `langchain_openai.OpenAIEmbeddings` | Embeddings | nova instância por ingestão |
| `langchain_text_splitters.RecursiveCharacterTextSplitter` | Chunking | `chunk_size=1000, chunk_overlap=200` |
| `pypdf.PdfReader` | Extração PDF | `mime_type == "application/pdf"` |
| `apps.common.exceptions.AppError` | Erros padronizados | `VALIDATION_ERROR`/`FILE_TOO_LARGE`/`INVALID_FILE_TYPE` |
| `apps.audit.services.log.record` | Auditoria (stub) | `KB_UPLOAD` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| IDs de chunk `"{document_id}-{i}-{uuid8}"` | `ingestion.py:48` | 🟢 |
| Ingestão síncrona no request | `views.py:45` | 🟢 |
| `ALLOWED_MIMETYPES`/`MAX_BYTES` hardcoded (não settings/env) | `ingestion.py:16-17` | 🟢 |
| `os.environ` lido fora de `settings.py` | `ingestion.py:34` | 🟢 |
| MIME confiado no header do cliente (`f.content_type`), sem sniffing | `views.py:32` | 🟢 |

## Riscos e Lacunas

- 🔴 Ingestão síncrona e sem throttle — arquivos grandes bloqueiam o worker; sem fila/celery.
- 🔴 Catch-all na ingestão rotula qualquer erro como falha de indexação (embedding/Chroma/rede não distinguidos).
- 🔴 Convenção de env violada (`os.environ[...]` em `ingestion.py:34`); `CHROMA_PERSIST_DIR` ausente → `KeyError` cru.
- 🟡 MIME confiado no header — arquivo renomeado passa na validação.
- 🟡 Embeddings recriados a cada ingestão vs singleton no retriever — padrão inconsistente.

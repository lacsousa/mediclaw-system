# RAG / Upload & Ingest — Requisitos

> Contrato operacional do caso de uso **Upload e ingestão de documento** (`POST /api/v1/admin/knowledge/upload/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Recebe um arquivo multipart (PDF/Markdown/TXT), cria um `KnowledgeDocument` (`status=PROCESSING`) e executa a ingestão **síncrona**: extração de texto, chunking, embeddings e gravação no ChromaDB. Encerra com `status=INDEXED` e `chunk_count` (ou `ERROR` com `error_message`).

## Regras de Negócio

- **RN-01** — Upload sem `file` → 400 `VALIDATION_ERROR`. 🟢
- **RN-02** — `size > 10MB` → 400 `FILE_TOO_LARGE`. 🟢
- **RN-03** — `mime_type` fora de `{application/pdf, text/markdown, text/plain}` → 400 `INVALID_FILE_TYPE`. 🟢
- **RN-04** — `title = (request.data.get("title") or f.name)[:200]`. 🟢
- **RN-05** — Ingestão síncrona no request (bloqueia o worker). 🟢
- **RN-06** — Texto vazio extraído → `ValueError` → `status=ERROR`. 🟢
- **RN-07** — Qualquer exceção na ingestão → `except Exception` → `status=ERROR`, `error_message=str(e)[:1000]`. 🟢
- **RN-08** — Sucesso → `status=INDEXED`, `chunk_count=len(chunks)`; `record("KB_UPLOAD", ...)` (stub). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Fazer upload | Must | POST multipart com `file` + `title` opcional → 201 `{id, title, status, chunk_count}` |
| RF-02 | Validar arquivo | Must | Ausente/ > 10MB/ MIME não aceito → 400 com código apropriado |
| RF-03 | Extrair texto | Must | PDF via `pypdf`; MD/TXT via `decode("utf-8", errors="replace")` |
| RF-04 | Chunkar e indexar | Must | `RecursiveCharacterTextSplitter(1000, 200)` → `OpenAIEmbeddings` → `coll.add` |
| RF-05 | Registrar falha | Must | Falha → `status=ERROR` com `error_message` truncado em 1000 |

## Critérios de Aceitação

```gherkin
Dado um arquivo PDF válido com texto
Quando faço POST em /api/v1/admin/knowledge/upload/ com multipart
Então recebo 201 com status=INDEXED e chunk_count > 0, e os chunks estão no vector store

Dado um upload sem arquivo
Quando faço POST em /api/v1/admin/knowledge/upload/
Então recebo 400 VALIDATION_ERROR

Dado um arquivo de 12MB
Quando faço POST em /api/v1/admin/knowledge/upload/
Então recebo 400 FILE_TOO_LARGE

Dado um arquivo .exe
Quando faço POST em /api/v1/admin/knowledge/upload/
Então recebo 400 INVALID_FILE_TYPE
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/rag/views.py:26-59` | `upload_document` | 🟢 |
| `apps/rag/services/ingestion.py:38-70` | `ingest` | 🟢 |
| `apps/rag/services/ingestion.py:20-42` | `_extract_text` | 🟢 |
| `apps/rag/services/ingestion.py:27-29` | `_split` | 🟢 |
| `apps/rag/models.py:5-33` | `KnowledgeDocument` | 🟢 |
| `apps/rag/services/ingestion.py:16-17` | `ALLOWED_MIMETYPES`, `MAX_BYTES` | 🟢 |

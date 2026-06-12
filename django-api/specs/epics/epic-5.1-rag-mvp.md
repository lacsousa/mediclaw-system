# Epic 5.1 — RAG Essencial (MVP)

> **Objetivo:** RAG funcionando com o mínimo necessário — o orquestrador consegue recuperar chunks relevantes para fundamentar as respostas.
> Referência: [TASKS.md](../TASKS.md) · [epic-5-rag.md](epic-5-rag.md) (detalhes técnicos completos)

---

## Dependências

- E1 (foundation), E4 (ai_engine — `orchestrator.generate` já usa `{rag_context}`)

---

## Story 5.1.1 — Vector Store

- [ ] `apps/rag/vector_store.py::get_collection()` singleton com ChromaDB persistente
- [ ] Lê `CHROMA_PERSIST_DIR` do `.env`
- [ ] `telemetry=False` no cliente Chroma

## Story 5.1.2 — Modelo KnowledgeDocument

- [ ] Modelo com campos: `title`, `file_name`, `mime_type`, `status`, `chunk_count`, `error_message`, `uploaded_by`, timestamps
- [ ] Status: `PROCESSING`, `INDEXED`, `ERROR`
- [ ] Migration criada e aplicada

## Story 5.1.3 — Pipeline de Ingestão

- [ ] `apps/rag/ingestion.py::ingest(document, file_bytes)` síncrono
- [ ] Extrai texto de PDF (`pypdf`) e TXT/MD (decode direto)
- [ ] Chunk com `RecursiveCharacterTextSplitter(size=1000, overlap=200)`
- [ ] Gera embeddings via `OpenAIEmbeddings` (ou provider configurado)
- [ ] Armazena no Chroma com metadados `document_id`, `title`, `chunk_index`
- [ ] Atualiza `status` e `chunk_count` no modelo

## Story 5.1.4 — Retriever

- [ ] `apps/rag/retriever.py::search(query, k=5, min_score=0.75) → list[dict]`
- [ ] Retorna `[]` se coleção vazia
- [ ] Converte distância cosseno do Chroma em score `[0,1]`
- [ ] Filtra chunks abaixo de `min_score`

## Story 5.1.5 — Healthcheck

- [ ] `GET /health` passa a retornar `vector_store: ok` (ou `error`)
- [ ] Atualiza o stub existente na Story 1.2

---

## Critérios de Aceite

- [ ] Rodar `ingest()` via shell Django indexa um TXT simples sem erros
- [ ] `retriever.search("texto relevante")` retorna o chunk indexado
- [ ] `retriever.search("off-topic")` retorna lista vazia
- [ ] `GET /health` exibe `vector_store: ok`

---

## Testes mínimos

```python
# tests/rag/test_ingestion.py
def test_ingest_txt_creates_indexed_document(): ...
def test_ingest_empty_file_sets_error_status(): ...

# tests/rag/test_retriever.py
def test_search_returns_chunk_after_indexing(): ...
def test_search_empty_collection_returns_empty(): ...
```

> **Dica:** usar `CHROMA_PERSIST_DIR=tmp_path` para isolar por teste; mockar embeddings com vetores fixos.

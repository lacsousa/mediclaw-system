# RAG / Upload & Ingest, Tarefas de Implementação

> Sequência executável para reimplementar upload/ingestão a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Modelo `KnowledgeDocument`
- [ ] `get_collection` singleton (ver collection-singleton)
- [ ] Deps: `pypdf`, `langchain_openai`, `langchain_text_splitters`

## Tarefas

- [ ] **T-01**, `_extract_text` com PDF via pypdf e MD/TXT via utf-8
  - Origem no legado: `apps/rag/services/ingestion.py:20-42`
  - Critério de pronto: texto vazio → `ValueError`
  - Confiança: 🟢

- [ ] **T-02**, `_split` com `RecursiveCharacterTextSplitter(1000, 200)`
  - Origem no legado: `apps/rag/services/ingestion.py:27-29`
  - Confiança: 🟢

- [ ] **T-03**, `ingest` com embeddings, `coll.add` e transição de status
  - Origem no legado: `apps/rag/services/ingestion.py:38-70`
  - Critério de pronto: sucesso → `INDEXED` + `chunk_count`; exceção → `ERROR` + `error_message[:1000]`
  - Confiança: 🟢

- [ ] **T-04**, View `upload_document` com validações de presença/tamanho/MIME
  - Origem no legado: `apps/rag/views.py:26-59`
  - Critério de pronto: 400 `VALIDATION_ERROR`/`FILE_TOO_LARGE`/`INVALID_FILE_TYPE`; 201 `{id, title, status, chunk_count}`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Upload PDF válido → 201 `INDEXED` com chunks no vector store
- [ ] **TT-02**, Upload sem arquivo → 400 `VALIDATION_ERROR`
- [ ] **TT-03**, Arquivo > 10MB → 400 `FILE_TOO_LARGE`
- [ ] **TT-04**, MIME não aceito → 400 `INVALID_FILE_TYPE`
- [ ] **TT-05**, Documento sem texto → status `ERROR` com `error_message`
- [ ] **TT-06**, Falha de embedding/Chroma → status `ERROR` (fluxo não quebra)

## Ordem Sugerida

1. T-01 → T-02 → T-03 → T-04.
2. Testes TT-01 a TT-06 (mockar OpenAIEmbeddings e ChromaDB).

## Lacunas Pendentes (🔴)

- [ ] Avaliar fila/worker para ingestão assíncrona (hoje síncrona no request).
- [ ] Distinguir causas de falha (substituir catch-all).
- [ ] Ler env via `settings.py` (convenção do projeto).
- [ ] Sniffing de MIME (não confiar só no header).

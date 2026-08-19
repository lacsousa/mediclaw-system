# RAG, Tarefas de Implementação

> Sequência executável para reimplementar a unit `rag` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Unit `common` implementada — `AppError` em `apps/common/exceptions.py` (code/message/status), `IsAdminRole` em `apps/common/permissions.py`
- [ ] Unit `accounts` implementada — model `User` (`apps.accounts.models.User`)
- [ ] Unit `conversations` implementada — model `Message` com `tokens_used` e `blocked_by_guardrail` (usado pelo `metrics`)
- [ ] Unit `audit` com `record(event, *, user=None, **kwargs)` (stub `pass` aceito no MVP)
- [ ] Dependências Python: `chromadb`, `langchain-openai`, `langchain-text-splitters`, `pypdf`, `overrides`
- [ ] Variáveis de ambiente: `CHROMA_PERSIST_DIR` (obrigatório), `EMBEDDING_MODEL` (default `text-embedding-3-small`), `ANONYMIZED_TELEMETRY` (default `False`), `RAG_TOP_K` (5), `RAG_MIN_SCORE` (0.75)
- [ ] Diretório `knowledge_base/` (docs fonte) e `chroma_data/` (persistência) existentes

## Tarefas

- [ ] **T-01**, Model `KnowledgeDocument`
  - Origem no legado: `apps/rag/models.py:5-33`
  - Critério de pronto: `title` (CharField 200), `file_name` (255), `mime_type` (80), `status` (choices `PROCESSING`/`INDEXED`/`ERROR`, default `PROCESSING`, max 12), `chunk_count` (PositiveIntegerField null/blank), `error_message` (TextField blank), `uploaded_by` (FK `AUTH_USER_MODEL`, `on_delete=SET_NULL`, null, related_name `knowledge_documents`), `created_at`/`updated_at` (auto); `Meta.ordering = ["-created_at"]`; migration commitada
  - Confiança: 🟢

- [ ] **T-02**, Telemetria ChromaDB desativada (`NoopProductTelemetry`)
  - Origem no legado: `apps/rag/telemetry_noop.py:8-14`
  - Critério de pronto: classe `NoopProductTelemetry(ProductTelemetryClient)` com `__init__(self, system: System)` e `capture(self, event)` que apenas retorna `None` (override)
  - Confiança: 🟢

- [ ] **T-03**, Vector store singleton `get_collection`
  - Origem no legado: `apps/rag/vector_store.py:7-34`
  - Critério de pronto: `COLLECTION_NAME = "mediclaw_kb"`; singletons module-scope `_lock` (threading.Lock), `_client`, `_collection`; `get_collection()` com double-checked locking — se `_collection` já existe retorna; senão lê `os.environ["CHROMA_PERSIST_DIR"]` (**sem fallback**), `os.makedirs(persist, exist_ok=True)`, `os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")`, `chromadb.PersistentClient(path=persist, settings=Settings(anonymized_telemetry=False, chroma_product_telemetry_impl="apps.rag.telemetry_noop.NoopProductTelemetry"))`, `_client.get_or_create_collection(COLLECTION_NAME)`; thread-safe
  - Confiança: 🟢

- [ ] **T-04**, Extração de texto `_extract_text`
  - Origem no legado: `apps/rag/ingestion.py:20-24`
  - Critério de pronto: `_extract_text(file_bytes, mime_type) -> str` — PDF → `PdfReader(BytesIO(file_bytes))`, junta `page.extract_text() or ""` de cada página com `"\n"`; MD/TXT → `file_bytes.decode("utf-8", errors="replace")`
  - Confiança: 🟢

- [ ] **T-05**, Chunking `_split` e embeddings `_get_embeddings`
  - Origem no legado: `apps/rag/ingestion.py:27-35`
  - Critério de pronto: `_split(text)` → `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_text(text)`; `_get_embeddings()` → `OpenAIEmbeddings(model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))` — **nova instância por chamada** (não é singleton)
  - Confiança: 🟢

- [ ] **T-06**, Ingestão `ingest`
  - Origem no legado: `apps/rag/ingestion.py:38-70`
  - Critério de pronto: `ingest(document, file_bytes) -> None` — `_extract_text`; texto vazio → `raise ValueError("Documento vazio ou sem texto extraível.")`; `_split`; `_get_embeddings().embed_documents(chunks)`; `coll.add(ids=[f"{document.id}-{i}-{uuid4().hex[:8]}"], documents=chunks, embeddings=vectors, metadatas=[{document_id: str(document.id), title: document.title, chunk_index: i}])`; sucesso → `status="INDEXED"`, `chunk_count=len(chunks)`, `error_message=""`, `save(update_fields=["status","chunk_count","error_message","updated_at"])`; **qualquer exceção** → `logger.exception("document_index_failed", document_id=document.id)`, `status="ERROR"`, `error_message=str(e)[:1000]`, `save(update_fields=["status","error_message","updated_at"])`
  - Confiança: 🟢

- [ ] **T-07**, Retrieval `search`
  - Origem no legado: `apps/rag/retriever.py:10-52`
  - Critério de pronto: `search(query, k=5, min_score=0.40) -> list[dict]` — singleton `_emb` (criado uma vez, `OpenAIEmbeddings` com `EMBEDDING_MODEL`); `coll.count() == 0` → `[]`; `qvec = _emb.embed_query(query)`; `coll.query(query_embeddings=[qvec], n_results=min(k, coll.count()), include=["documents","metadatas","distances"])`; para cada resultado: `score = max(0.0, 1.0 - (dist/2.0))`, descarta `score < min_score`; retorna `{content, source: meta.get("title", "desconhecida"), chunk_id: str(meta.get("chunk_index", "")), document_id: meta.get("document_id"), score: round(score, 4)}`
  - Confiança: 🟢

- [ ] **T-08**, View `upload`
  - Origem no legado: `apps/rag/views.py:23-59`
  - Critério de pronto: `@api_view(["POST"])`, `@permission_classes([IsAuthenticated])`, `@parser_classes([MultiPartParser])` — `f = request.FILES.get("file")`; ausente → `AppError("VALIDATION_ERROR", "Arquivo ausente.", 400)`; `f.size > MAX_BYTES` (10MB) → `AppError("FILE_TOO_LARGE", ..., 400)`; `f.content_type not in ALLOWED_MIMETYPES` (`{"application/pdf","text/markdown","text/plain"}`) → `AppError("INVALID_FILE_TYPE", ...)`; `title = (request.data.get("title") or f.name)[:200]`; cria `KnowledgeDocument(status="PROCESSING", uploaded_by=request.user)`; `ingest(doc, f.read())`; `record("KB_UPLOAD", user=request.user, metadata={"document_id": doc.id, "status": doc.status})`; retorna 201 `{id, title, status, chunk_count}`
  - Confiança: 🟢

- [ ] **T-09**, View `list_documents`
  - Origem no legado: `apps/rag/views.py:62-68`
  - Critério de pronto: `@api_view(["GET"])` + `IsAuthenticated` — `KnowledgeDocument.objects.values("id", "title", "status", "chunk_count", "created_at")` → lista (ordering `-created_at` do model)
  - Confiança: 🟢

- [ ] **T-10**, View `document_status`
  - Origem no legado: `apps/rag/views.py:71-85`
  - Critério de pronto: `@api_view(["GET"])` + `IsAuthenticated` — busca por `pk`; `DoesNotExist` → `AppError("NOT_FOUND", "Documento não encontrado.", 404)`; retorna `{id, status, chunk_count, error_message}`
  - Confiança: 🟢

- [ ] **T-11**, View `delete_document`
  - Origem no legado: `apps/rag/views.py:117-131`
  - Critério de pronto: `@api_view(["DELETE"])` + `IsAuthenticated` — busca por `pk`; `DoesNotExist` → 404; `status == "PROCESSING"` → `AppError("CONFLICT", "Documento em processamento; aguarde concluir.", 409)`; `get_collection().delete(where={"document_id": str(doc.id)})`; `doc.delete()`; `record("KB_DELETE", user=request.user, metadata={"document_id": doc_id})`; retorna 204
  - Confiança: 🟢

- [ ] **T-12**, View `metrics` (admin)
  - Origem no legado: `apps/rag/views.py:88-114`
  - Critério de pronto: `@api_view(["GET"])` + `@permission_classes([IsAdminRole])` — `tokens_today` = `Sum("tokens_used")` de `Message` de hoje; `messages_today`; `guardrail_blocks_today` (`blocked_by_guardrail=True`); `users_total`; `conversations_total`; `kb_documents_indexed` (`status="INDEXED"`); retorna dict agregado. A rota é registrada em `apps/audit/urls.py:9` (`path("metrics/", metrics)`) → `/api/v1/admin/metrics/` — **não** em `apps/rag/urls.py`.
  - Confiança: 🟢

- [ ] **T-13**, Rotas `apps/rag/urls.py` e montagem no projeto
  - Origem no legado: `apps/rag/urls.py:10-15`; `config/urls.py:35`
  - Critério de pronto: `path("upload/", upload)`, `path("", list_documents)`, `path("<int:doc_id>/status/", document_status)`, `path("<int:doc_id>/", delete_document)`; montagem `path("api/v1/admin/knowledge/", include("apps.rag.urls"))` no `config/urls.py`. **Nota:** `metrics` é montado fora deste urlconf — fica em `apps/audit/urls.py:9` (`/api/v1/admin/metrics/`)
  - Confiança: 🟢

- [ ] **T-14**, Eventos de auditoria `KB_UPLOAD` / `KB_DELETE`
  - Origem no legado: `apps/rag/views.py:46-50,130-131`
  - Critério de pronto: `record("KB_UPLOAD", user=request.user, metadata={document_id, status})` após upload; `record("KB_DELETE", user=request.user, metadata={document_id})` após delete — compatível com a assinatura `record(event, *, user=None, **kwargs)`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Upload happy path (PDF 500KB, `application/pdf`) → 201 com `status="INDEXED"` e `chunk_count > 0`; registro criado com `uploaded_by=request.user`
- [ ] **TT-02**, Upload sem arquivo → 400 `VALIDATION_ERROR`
- [ ] **TT-03**, Upload > 10MB → 400 `FILE_TOO_LARGE`
- [ ] **TT-04**, Upload com `content_type=image/png` → 400 `INVALID_FILE_TYPE`
- [ ] **TT-05**, Upload de PDF sem camada de texto → `ingest` deixa status `ERROR` com `error_message` contendo "Documento vazio" (resposta 201 reflete `ERROR`)
- [ ] **TT-06**, Upload de MD/TXT com texto válido → `INDEXED`, chunks com IDs `"{doc_id}-{i}-{uuid8}"` e metadatas `{document_id, title, chunk_index}`
- [ ] **TT-07**, `list_documents` → lista ordenada por `-created_at` com os 5 campos
- [ ] **TT-08**, `document_status` de doc inexistente → 404 `NOT_FOUND`; de doc `ERROR` → inclui `error_message`
- [ ] **TT-09**, `delete_document` de doc `PROCESSING` → 409 `CONFLICT`
- [ ] **TT-10**, `delete_document` de doc `INDEXED` → 204 e coleção ChromaDB sem chunks com `document_id` correspondente (mockar `coll.delete` e verificar `where`)
- [ ] **TT-11**, `search` com coleção vazia → `[]`
- [ ] **TT-12**, `search` com `min_score` alto → nenhum chunk retornado quando todos abaixo do limiar
- [ ] **TT-13**, `search` converte distância: chunk com dist=0 → `score=1.0`; dist=2 → `score=0.0` (mockar query do ChromaDB)
- [ ] **TT-14**, `search` limita `n_results=min(k, coll.count())` — pedir k maior que o total não quebra
- [ ] **TT-15**, `get_collection` é singleton: duas chamadas retornam a mesma coleção; segunda chamada não reconstrói o cliente
- [ ] **TT-16**, `get_collection` sem `CHROMA_PERSIST_DIR` no env → `KeyError` (documentar comportamento atual)
- [ ] **TT-17**, `metrics` em `/api/v1/admin/metrics/` com role `ADMIN` → 200 com os 6 agregados; com role não-ADMIN → 403 `FORBIDDEN`
- [ ] **TT-18**, Nenhum log contém conteúdo do documento (inspecionar payload de `document_index_failed`)

## Tarefas de Migração de Dados (se aplicável)

- [ ] **TM-01**, Se houver ChromaDB pré-existente em `CHROMA_PERSIST_DIR`, validar compatibilidade de metadatas e IDs com o novo schema — o legado usa IDs `"{doc_id}-{i}-{uuid8}"` e metadatas `{document_id, title, chunk_index}` (`ingestion.py:48-56`); sem isso, a coleção `mediclaw_kb` é recriável do zero via re-ingestão da `knowledge_base/`
  - Confiança: 🟢

## Ordem Sugerida

1. T-01 (model) → T-02/T-03 (telemetria + vector store): base sem dependências externas além do ChromaDB; testável isolada (TT-15/TT-16).
2. T-04 → T-06 (extração → chunking/embeddings → ingest): dependem de T-03; mockar chamadas de embedding nos testes.
3. T-07 (search): depende de T-03; consumido pelo `ai_engine` (`orchestrator._build_messages`).
4. T-08 → T-12 (views) + T-13 (rotas): dependem de T-01, `common` (`AppError`, `IsAdminRole`), `accounts.User`, `conversations.Message`, `audit.record`.
5. T-14 (auditoria) pode acompanhar as views — stub `pass` aceito no MVP.
6. Testes na ordem das dependências: TT-01–TT-06 (upload/ingest) → TT-07–TT-10 (list/status/delete) → TT-11–TT-16 (search/store) → TT-17–TT-18 (metrics/privacidade).
7. **Antes do deploy:** alinhar a documentação da rota `metrics` (real: `/api/v1/admin/metrics/`, via `apps/audit/urls.py`) com o contrato — ver Lacuna 1.

## Lacunas Pendentes (🔴)

- [ ] **Path documentado ≠ path real do `metrics`:** o contrato documenta `/api/v1/admin/knowledge/metrics/`, mas a rota real é `/api/v1/admin/metrics/` (via `apps/audit/urls.py:9`, montada em `config/urls.py:36`). Alinhar o `requirements.md` ao caminho real e validar se `metrics` permanece no roteador do `audit` (que funciona como roteador admin) ou migra para o app `rag`.
- [ ] **Acesso não escopado ao uploader:** status/delete buscam por `pk` sem filtrar `uploaded_by` (`views.py:73-77,119-123`) — qualquer autenticado lê/deleta documentos de terceiros. Decidir se restringir ao uploader ou a admins.
- [ ] **`document_status` expõe `error_message`** (`views.py:78-84`) — potencial vazamento de detalhes internos. Definir se mascarar a mensagem para não-admins.
- [ ] **Ingestão síncrona no request** (`views.py:45`) — arquivos grandes bloqueiam o worker; decidir se o MVP aceita ou move para fila/worker.
- [ ] **Catch-all na ingestão** (`ingestion.py:66-70`) mascara a causa raiz; refinar tratamento de exceções (embedding vs ChromaDB vs rede).
- [ ] **Leitura direta de `os.environ`** em `vector_store.py:21`, `ingestion.py:34`, `retriever.py:14` viola a convenção do projeto (env só em `settings.py`); `CHROMA_PERSIST_DIR` ausente → `KeyError` cru.
- [ ] **Divergência de `min_score`:** default de `search` é `0.40` (`retriever.py:19`) vs `RAG_MIN_SCORE=0.75` documentado — alinhar o default ao contrato.

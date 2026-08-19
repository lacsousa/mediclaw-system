# RAG, Design Técnico

> Contrato operacional de **COMO** a unit `rag` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

A unit expõe endpoints HTTP sob `/api/v1/admin/knowledge/` (montada em `config/urls.py:35`), além de funções de serviço (`ingest`, `search`, `get_collection`) consumidas pela própria unit e pelo `ai_engine`.

### Endpoints HTTP

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| POST | `/api/v1/admin/knowledge/upload/` | `file` (multipart) + `title` opcional | `{id, title, status, chunk_count}` | 201, 400 (`VALIDATION_ERROR`/`FILE_TOO_LARGE`/`INVALID_FILE_TYPE`) |
| GET | `/api/v1/admin/knowledge/` | — | lista de `{id, title, status, chunk_count, created_at}` | 200 |
| GET | `/api/v1/admin/knowledge/<doc_id>/status/` | `doc_id: int` | `{id, status, chunk_count, error_message}` | 200, 404 (`NOT_FOUND`) |
| DELETE | `/api/v1/admin/knowledge/<doc_id>/` | `doc_id: int` | `204` | 204, 404, 409 (`CONFLICT`) |
| GET | `/api/v1/admin/metrics/` | — | `{users_total, conversations_total, messages_today, tokens_today, guardrail_blocks_today, kb_documents_indexed}` | 200, 403 (`FORBIDDEN`) |

> ⚠️ **Path do `metrics` ≠ documentado no `requirements.md`:** a view `metrics` (`views.py:88-114`) **não está registrada** em `apps/rag/urls.py:10-15`, mas é importada e registrada em `apps/audit/urls.py:9` (`path("metrics/", metrics)`), montada em `/api/v1/admin/` (`config/urls.py:36`). O caminho real é **`/api/v1/admin/metrics/`** — e não `/api/v1/admin/knowledge/metrics/` como consta no `requirements.md` (que responde 404).

### Funções / classes públicas

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `ingest` | `(document: KnowledgeDocument, file_bytes: bytes) -> None` | `None` | Extrai texto, chunking, embeddings e grava no ChromaDB; atualiza status (`ingestion.py:38-70`) |
| `search` | `(query: str, k: int = 5, min_score: float = 0.40) -> list[dict]` | chunks `{content, source, chunk_id, document_id, score}` | Retrieval por similaridade L² (`retriever.py:19-52`) |
| `get_collection` | `() -> Collection` | coleção ChromaDB `mediclaw_kb` | Singleton thread-safe (`vector_store.py:14-34`) |
| `_extract_text` | `(file_bytes: bytes, mime_type: str) -> str` | texto bruto | PDF via `pypdf`; MD/TXT via decode utf-8 (`ingestion.py:20-24`) |
| `_split` | `(text: str) -> list[str]` | chunks | `RecursiveCharacterTextSplitter(1000, 200)` (`ingestion.py:27-29`) |
| `NoopProductTelemetry.capture` | `(event: ProductTelemetryEvent) -> None` | `None` | Telemetria ChromaDB desativada (`telemetry_noop.py:8-14`) |

### Modelo de dados

| Modelo | Campos | Fonte |
|--------|--------|-------|
| `KnowledgeDocument` | `title`, `file_name`, `mime_type`, `status` (`PROCESSING`/`INDEXED`/`ERROR`), `chunk_count`, `error_message`, `uploaded_by` (FK user, `SET_NULL`), `created_at`, `updated_at` | `models.py:5-33` |

## Fluxo Principal

### 1. Upload + ingestão síncrona (`views.py:26-59` → `ingestion.py:38-70`)

1. Valida presença de `file` no multipart; ausente → `VALIDATION_ERROR` 400. (`views.py:27-29`) 🟢
2. Valida `f.size <= MAX_BYTES` (10MB); acima → `FILE_TOO_LARGE` 400. (`views.py:30-31`) 🟢
3. Valida `f.content_type ∈ ALLOWED_MIMETYPES` (`application/pdf`, `text/markdown`, `text/plain`); fora → `INVALID_FILE_TYPE` 400. (`views.py:32-35`, `ingestion.py:16`) 🟢
4. `title = (request.data.get("title") or f.name)[:200]`; cria `KnowledgeDocument(status="PROCESSING", uploaded_by=request.user)`. (`views.py:37-44`) 🟢
5. `ingest(doc, f.read())` — **síncrono no request**. (`views.py:45`) 🟢
   - `_extract_text`: PDF → junta `page.extract_text()` de cada página; MD/TXT → `decode("utf-8", errors="replace")`. Texto vazio → `ValueError`. (`ingestion.py:20-42`) 🟢
   - `_split`: `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`. (`ingestion.py:27-29`) 🟢
   - `_get_embeddings()`: `OpenAIEmbeddings(model=env EMBEDDING_MODEL, default text-embedding-3-small)` — nova instância a cada ingestão. (`ingestion.py:32-35`) 🟢
   - `coll.add(ids=["{doc_id}-{i}-{uuid8}"], documents=chunks, embeddings=vectors, metadatas=[{document_id, title, chunk_index}])`. (`ingestion.py:47-57`) 🟢
   - Sucesso → `status="INDEXED"`, `chunk_count=len(chunks)`. Falha (qualquer exceção) → log `document_index_failed`, `status="ERROR"`, `error_message=str(e)[:1000]`. (`ingestion.py:59-70`) 🟢
6. `record("KB_UPLOAD", user=request.user, metadata={document_id, status})` — **stub** no MVP. (`views.py:46-50`) 🟢
7. Retorna 201 com `{id, title, status, chunk_count}`. (`views.py:51-59`) 🟢

### 2. Retrieval — `search` (`retriever.py:19-52`)

1. `coll = get_collection()`; se `coll.count() == 0` → `[]`. (`retriever.py:25-27`) 🟢
2. `qvec = _get_embeddings().embed_query(query)` — embeddings em **cache singleton** (`_emb` module-scope). (`retriever.py:7-16,29`) 🟢
3. `coll.query(query_embeddings=[qvec], n_results=min(k, coll.count()), include=["documents", "metadatas", "distances"])`. (`retriever.py:30-34`) 🟢
4. Para cada resultado, converte distância L² → score: `max(0.0, 1.0 - (dist / 2.0))`; descarta `score < min_score`. (`retriever.py:40-42`) 🟡 (fórmula depende de vetores normalizados — hipótese não fixada na coleção) [Revisão Codex]
5. Monta `{content, source=title, chunk_id=chunk_index, document_id, score=round(score, 4)}`. (`retriever.py:43-51`) 🟢

### 3. Listagem / Status / Delete

1. `list_documents`: `KnowledgeDocument.objects.values("id", "title", "status", "chunk_count", "created_at")` → lista (ordering do model `-created_at`). (`views.py:62-68`, `models.py:29-30`) 🟢
2. `document_status`: busca por `pk`; inexistente → `NOT_FOUND` 404; retorna `{id, status, chunk_count, error_message}`. (`views.py:71-85`) 🟢
3. `delete_document`: busca por `pk`; inexistente → 404; **`status == "PROCESSING"` → `CONFLICT` 409**. (`views.py:117-125`) 🟢
4. `coll.delete(where={"document_id": str(doc.id)})` → remove chunks do vector store → `doc.delete()`. (`views.py:127-129`) 🟢
5. `record("KB_DELETE", user, metadata={document_id})` — stub; retorna 204. (`views.py:130-131`) 🟢

### 4. Métricas admin — `metrics` (`views.py:88-114`)

1. Agrega por data de hoje: `tokens_today` = `Sum("tokens_used")` sobre `Message` de hoje; `messages_today`; `guardrail_blocks_today` (`blocked_by_guardrail=True`). (`views.py:93-107`) 🟢
2. `users_total` (`User.objects.count()`), `conversations_total`, `kb_documents_indexed` (`KnowledgeDocument` com `status="INDEXED"`). (`views.py:101-112`) 🟢
3. A rota é exposta via **`apps/audit/urls.py:9`** (`path("metrics/", metrics)`), montada em `/api/v1/admin/` — caminho real `/api/v1/admin/metrics/`. `IsAdminRole` restringe a role `ADMIN`. 🟢

## Fluxos Alternativos

- **[Arquivo ausente no upload]:** `AppError("VALIDATION_ERROR", "Arquivo ausente.", 400)`. 🟢
- **[Arquivo > 10MB]:** `AppError("FILE_TOO_LARGE", ..., 400)`. 🟢
- **[MIME não permitido]:** `AppError("INVALID_FILE_TYPE", ..., 400)` com o tipo recebido na mensagem. 🟢
- **[Documento inexistente (status/delete)]:** `AppError("NOT_FOUND", ..., 404)`. 🟢
- **[Delete durante PROCESSING]:** `AppError("CONFLICT", ..., 409)` — documenta "aguarde concluir". 🟢
- **[Documento sem texto extraível]:** `ValueError("Documento vazio ou sem texto extraível.")` → status `ERROR`. 🟢
- **[Falha em qualquer etapa da ingestão]:** `except Exception` → `logger.exception("document_index_failed")`, status `ERROR`, `error_message=str(e)[:1000]`. 🟢
- **[Coleção vazia no search]:** retorna `[]`. 🟢
- **[Score abaixo do mínimo]:** chunk descartado (`continue`). 🟢
- **[`CHROMA_PERSIST_DIR` ausente do env]:** `os.environ["CHROMA_PERSIST_DIR"]` levanta `KeyError` em `get_collection` — não há fallback. 🟢 (lacuna de configuração)

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| ChromaDB `PersistentClient` | Vector store local persistente | `get_collection` cria cliente + coleção `mediclaw_kb` no path de `CHROMA_PERSIST_DIR` (`vector_store.py:14-34`) |
| `langchain_openai.OpenAIEmbeddings` | Embeddings dos chunks e da query | `ingestion._get_embeddings` (nova por ingestão) e `retriever._get_embeddings` (singleton `_emb`) |
| `langchain_text_splitters.RecursiveCharacterTextSplitter` | Chunking | `_split(text)` com `chunk_size=1000, chunk_overlap=200` (`ingestion.py:27-29`) |
| `pypdf.PdfReader` | Extração de texto de PDF | `_extract_text` para `mime_type == "application/pdf"` (`ingestion.py:20-24`) |
| `apps.common.exceptions.AppError` | Erros de API padronizados | Views levantam com `code`, `message`, HTTP status (`views.py:29,31,34,77,123,125`) |
| `apps.common.permissions.IsAdminRole` | Restrição de role | `metrics` exige role `ADMIN` (`views.py:89`) |
| `apps.audit.services.log.record` | Auditoria | `KB_UPLOAD`/`KB_DELETE` — **stub `pass`** no MVP |
| `apps.accounts.models.User` | Contagem de usuários | `metrics` (`views.py:101`) |
| `apps.conversations.models.Conversation`, `Message` | Métricas de conversas/mensagens | `metrics` agrega `tokens_used`, `blocked_by_guardrail` por dia (`views.py:93-107`) |
| `apps.ai_engine.orchestrator._build_messages` | Consumidor do retrieval | `search(query, k=RAG_TOP_K, min_score=RAG_MIN_SCORE)` injeta chunks no system prompt |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Vector store como **singleton thread-safe** com double-checked locking | `vector_store.py:7-34` | 🟢 |
| **Telemetria ChromaDB desativada** via `NoopProductTelemetry` (evita incompatibilidade posthog 7.x) | `telemetry_noop.py:1-14`; `vector_store.py:23-31` | 🟢 |
| IDs de chunk estruturados `"{document_id}-{index}-{uuid8}"` para rastreabilidade e delete por `where` | `ingestion.py:48` | 🟢 |
| Conversão de distância L² → score `max(0.0, 1.0 - dist/2.0)` (equivale a cosseno só com vetores normalizados — hipótese não fixada no metadata da coleção) | `retriever.py:22-23,40` | 🟡 [Revisão Codex] |
| **Ingestão síncrona no request** (upload bloqueia o worker até terminar) | `views.py:45` | 🟢 |
| Upload valida MIME e tamanho no backend com **constantes hardcoded** (`ALLOWED_MIMETYPES`, `MAX_BYTES`) em vez de settings/env | `ingestion.py:16-17` | 🟢 |
| **Leitura direta de `os.environ`** fora de `settings.py` — viola a convenção do projeto | `ingestion.py:34`, `retriever.py:14`, `vector_store.py:21-23` | 🟢 |
| Acesso a documentos **não escopado ao uploader** — qualquer autenticado lê/deleta qualquer documento | `views.py:73-77,119-123` | 🟢 |
| `metrics` definida na unit `rag` mas **registrada no urlconf do `audit`** (`apps/audit/urls.py:9`) — o app `audit` funciona como roteador admin | `views.py:88-114`; `apps/audit/urls.py:9`; `config/urls.py:36` | 🟢 |
| Default da assinatura `search(..., min_score=0.40)` diverge do env `RAG_MIN_SCORE` (0.75 no `.env.example`) | `retriever.py:19`; `orchestrator.py:126-128` | 🟡 |

## Estado Interno

- **`KnowledgeDocument`** (tabela `rag_knowledgedocument`): estado de cada documento com transição `PROCESSING → INDEXED | ERROR`. `chunk_count` `null` até `INDEXED`. `error_message` truncado em 1000 chars. 🟢
- **Coleção ChromaDB `mediclaw_kb`** persistida em `CHROMA_PERSIST_DIR` (volume Docker); contém chunks com metadatas `{document_id, title, chunk_index}`. 🟢
- **Singleton module-scope:** `_client`, `_collection` (`vector_store.py:8-9`) e `_emb` (`retriever.py:7`). Inicializados sob demanda (lazy) na primeira chamada; sobrevivem ao ciclo do worker. 🟢
- **Env consumido:** `CHROMA_PERSIST_DIR` (obrigatório), `EMBEDDING_MODEL` (default `text-embedding-3-small`), `ANONYMIZED_TELEMETRY` (setdefault `False`). 🟢

## Observabilidade

- Log estruturado de falha de indexação: `logger.exception("document_index_failed", document_id=document.id)` — sem conteúdo de documento (não loga PII). (`ingestion.py:67`) 🟢
- Eventos de auditoria `KB_UPLOAD` e `KB_DELETE` via `record` — **stub `pass`**, nada é persistido no MVP. 🟢
- **Sem logs de sucesso** em upload/delete/search; sem métricas de latência ou de recuperação. 🟡
- Endpoint de métricas agregadas disponível em `/api/v1/admin/metrics/` (role `ADMIN`) — agrega diariamente mensagens, tokens, guardrails e documentos indexados. 🟢

## Riscos e Lacunas

- 🟡 **Path documentado ≠ path real do `metrics`:** o `requirements.md` documenta `GET /api/v1/admin/knowledge/metrics/`, mas a rota real é `/api/v1/admin/metrics/` (registrada em `apps/audit/urls.py:9`, montada em `config/urls.py:36`). O path `.../knowledge/metrics/` responde 404.
- 🔴 **Acesso cruzado entre usuários:** status/detail/delete buscam por `pk` sem escopo ao `uploaded_by` (`views.py:73-77,119-123`) — qualquer autenticado pode ler metadados/`error_message` e deletar documentos de terceiros.
- 🔴 **`document_status` expõe `error_message`** ao consumidor (`views.py:78-84`) — potencial vazamento de detalhes internos (caminhos, libs) em falha de indexação.
- 🔴 **Ingestão síncrona e sem throttle:** `ingest(doc, f.read())` no corpo do request (`views.py:45`) — arquivos grandes/muitos documentos bloqueiam o worker; sem fila/worker/celery.
- 🔴 **Catch-all na ingestão:** `except Exception` rotula qualquer erro como falha de indexação (`ingestion.py:66-70`) — inclui erros de embedding, ChromaDB e de rede, sem distinguir causa.
- 🔴 **Convenção de env violada:** `os.environ[...]` acessado diretamente em `vector_store.py:21`, `ingestion.py:34`, `retriever.py:14` (a convenção do projeto é ler env apenas em `settings.py`). `CHROMA_PERSIST_DIR` ausente → `KeyError` cru sem mensagem amigável.
- 🟡 **Divergência de `min_score`:** default da função `search` é `0.40` (`retriever.py:19`), mas o contrato/env documenta `RAG_MIN_SCORE=0.75` — chamadas sem o argumento usam limiar diferente do configurado.
- 🟡 **`ANONYMIZED_TELEMETRY` via `setdefault`** (`vector_store.py:23`) não sobrescreve valor já presente no ambiente; se o ambiente definiu `True`, a telemetria fica ligada apesar da intenção do código.
- 🟡 **MIME confiado no header do cliente** (`f.content_type`), sem sniffing do conteúdo (`views.py:32`) — um arquivo renomeado passa na validação.
- 🟡 **Embeddings recriados a cada ingestão** (`ingestion.py:32-35`) vs singleton no retriever — inconsistência de padrão e custo extra de importação.

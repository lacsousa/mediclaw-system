# RAG — Requisitos

> Contrato operacional da unit `rag` (knowledge base + retrieval).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Knowledge base do MediClaw: ingestão de documentos (PDF, Markdown, TXT) com chunking e embeddings OpenAI, persistência em ChromaDB local (`mediclaw_kb`), e retrieval por similaridade usado pela camada de IA (`ai_engine`) para contextualizar respostas com citações. Expõe API de upload/listagem/status/delete de documentos sob `/api/v1/admin/knowledge/` e um endpoint de métricas admin em `/api/v1/admin/metrics/` (montado via `apps/audit/urls.py`, view `metrics` em `apps/rag/views.py`). 🟢 [Revisão Codex]

## Responsabilidades

- Ingerir documentos: extrair texto (PDF via `pypdf`, MD/TXT via decode utf-8), validar tamanho ≤ 10MB e MIME (pdf/markdown/plain), chunking `RecursiveCharacterTextSplitter` (1000/200), embedding `text-embedding-3-small`, gravar no ChromaDB
- Registrar o documento em `KnowledgeDocument` (status `PROCESSING` → `INDEXED`/`ERROR`)
- Recuperar chunks relevantes: `search(query, k, min_score)` com conversão de distância L² → score de similaridade
- Gerenciar o vector store ChromaDB como singleton thread-safe (path de `CHROMA_PERSIST_DIR`), com telemetria desativada
- Expor API de upload, listagem, status, delete e métricas admin
- Registrar eventos `KB_UPLOAD`/`KB_DELETE` via `record` — stub no MVP

## Regras de Negócio

- **RN-01** — Upload aceita apenas `application/pdf`, `text/markdown`, `text/plain` (`ALLOWED_MIMETYPES`); arquivo > 10MB (`MAX_BYTES`) → `FILE_TOO_LARGE`; MIME não permitido → `INVALID_FILE_TYPE`. 🟢
- **RN-02** — Documento inicia com status `PROCESSING`; após ingestão bem-sucedida → `INDEXED` com `chunk_count`; falha → `ERROR` com `error_message` (truncado em 1000 chars). 🟢
- **RN-03** — Texto extraído vazio → `ValueError` → status `ERROR` (`"Documento vazio ou sem texto extraível."`). 🟢
- **RN-04** — IDs dos chunks no ChromaDB: `"{document_id}-{index}-{uuid8}"`; metadatas: `document_id`, `title`, `chunk_index`. 🟢
- **RN-05** — `search` converte distância L² (ChromaDB) para score: `score = max(0.0, 1.0 - (dist / 2.0))`; chunks com `score < min_score` são descartados; retorna `{content, source (title), chunk_id, document_id, score}`. 🟢
- **RN-06** — `search` com coleção vazia (`coll.count() == 0`) → `[]`. 🟢
- **RN-07** — `n_results` limitado a `min(k, coll.count())`. 🟢
- **RN-08** — Delete rejeita documento em `PROCESSING` → `CONFLICT` 409; senão remove chunks do ChromaDB (`where={"document_id": ...}`) e o registro. 🟢
- **RN-09** — `uploaded_by` registrado no upload; **mas** status/detail/delete de documentos **não são escopados** ao uploader — qualquer autenticado lê/deleta qualquer documento. 🟢 (risco de segurança)
- **RN-10** — Métricas (`metrics`) exige `IsAdminRole` (role `ADMIN`); as demais rotas usam apenas `IsAuthenticated`. 🟢
- **RN-11** — `document_status` retorna `error_message` ao consumidor (potencial vazamento de detalhes internos de erro). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Upload de documento (multipart) | Must | `POST /api/v1/admin/knowledge/upload/` com `file` → 201 `{id, title, status, chunk_count}`; inválido → 400 com código específico |
| RF-02 | Listar documentos | Must | `GET /api/v1/admin/knowledge/` → lista de `{id, title, status, chunk_count, created_at}` (ordenada por `-created_at`) |
| RF-03 | Consultar status de um documento | Must | `GET /api/v1/admin/knowledge/<doc_id>/status/` → `{id, status, chunk_count, error_message}`; inexistente → 404 `NOT_FOUND` |
| RF-04 | Deletar documento (com remoção de chunks) | Must | `DELETE /api/v1/admin/knowledge/<doc_id>/` → 204; em `PROCESSING` → 409 `CONFLICT`; inexistente → 404 |
| RF-05 | Recuperar chunks relevantes para o orquestrador | Must | `search(query, k=RAG_TOP_K, min_score=RAG_MIN_SCORE)` → `list[dict]` com `content`, `source`, `chunk_id`, `document_id`, `score` |
| RF-06 | Ingerir documento com PDF/MD/TXT | Must | `ingest(document, file_bytes)` extrai texto, faz chunking, embeds e grava no ChromaDB; atualiza status para `INDEXED` |
| RF-07 | Métricas operacionais (admin) | Should | `GET /api/v1/admin/metrics/` → `{users_total, conversations_total, messages_today, tokens_today, guardrail_blocks_today, kb_documents_indexed}` (somente role `ADMIN`) |
| RF-08 | Telemetria ChromaDB desativada | Should | `get_collection()` configura `anonymized_telemetry=False` e cliente `NoopProductTelemetry` |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | Upload valida MIME e tamanho **server-side**, mas a checagem usa `f.content_type` (header controlado pelo cliente), **sem sniffing/magic bytes** — a garantia de tipo é declarativa, não inspecionada | `views.py:30-35` | 🟡 [Revisão Codex] |
| Segurança | `upload`/`list`/`status`/`delete` sob `/api/v1/admin/knowledge/` aceitam **qualquer autenticado**; `metrics` fica em `/api/v1/admin/metrics/` (audit.urls) e é o único restrito por role (`IsAdminRole`) | `config/urls.py:35`; `apps/audit/urls.py:8`; `apps/rag/views.py:24,63,72,90,118` | 🟢 [Revisão Codex] |
| Segurança | `document_status` e `delete_document` buscam por `pk` **sem escopo ao uploader** — acesso cruzado entre médicos | `views.py:73-77,119-123` | 🟢 |
| Privacidade | Telemetria do ChromaDB desativada (env `ANONYMIZED_TELEMETRY=False` + Noop) | `vector_store.py:23-31`; `telemetry_noop.py` | 🟢 |
| Desempenho | Chunking com `chunk_size=1000, chunk_overlap=200` (contexto das citações) | `ingestion.py:28` | 🟢 |
| Desempenho | Ingestão **síncrona** no request (`ingest(doc, f.read())`) — arquivos grandes bloqueiam o worker | `views.py:45` | 🟢 |
| Desempenho | `search` limita `n_results=min(k, coll.count())`; embeddings em cache singleton (`_emb`) | `retriever.py:31`; `vector_store.py` | 🟢 |
| Disponibilidade | Qualquer exceção na ingestão → status `ERROR` com mensagem (não derruba o request de forma crua) | `ingestion.py:66-70` | 🟢 |
| Integração | Embeddings OpenAI (`EMBEDDING_MODEL` default `text-embedding-3-small`) | `ingestion.py:32-35`; `retriever.py:10-16` | 🟢 |
| Observabilidade | Falha de indexação logada com `logger.exception("document_index_failed", document_id=...)` | `ingestion.py:67` | 🟢 |

## Critérios de Aceitação

```gherkin
# Upload — happy path (PDF)
Dado um arquivo PDF de 500KB com content_type application/pdf
Quando chamo POST /api/v1/admin/knowledge/upload/
Então retorna 201 com status "INDEXED" e chunk_count > 0

# Upload — arquivo grande
Dado um arquivo com size > 10MB
Quando chamo POST /api/v1/admin/knowledge/upload/
Então retorna 400 com code FILE_TOO_LARGE

# Upload — tipo inválido
Dado um arquivo com content_type image/png
Quando chamo POST /api/v1/admin/knowledge/upload/
Então retorna 400 com code INVALID_FILE_TYPE

# Upload — documento sem texto extraível
Dado um PDF sem camada de texto
Quando chamo ingest(doc, file_bytes)
Então doc.status == "ERROR" e error_message contém "Documento vazio"

# Listagem
Dado 3 documentos indexados
Quando chamo GET /api/v1/admin/knowledge/
Então retorna 3 itens com {id, title, status, chunk_count, created_at} ordenados por -created_at

# Status — inexistente
Dado doc_id inexistente
Quando chamo GET /api/v1/admin/knowledge/9999/status/
Então retorna 404 NOT_FOUND

# Delete — processando
Dado um documento com status PROCESSING
Quando chamo DELETE /api/v1/admin/knowledge/<id>/
Então retorna 409 CONFLICT

# Delete — happy path
Dado um documento INDEXED
Quando chamo DELETE /api/v1/admin/knowledge/<id>/
Então retorna 204 e a coleção ChromaDB não tem mais chunks com document_id=<id>

# Search — retorna chunks com score
Dado uma coleção com 3 chunks sobre "sono" e query "qualidade do sono"
Quando chamo search("qualidade do sono", k=5, min_score=0.4)
Então retorna lista de dicts com content, source, chunk_id, document_id e score >= 0.4

# Search — coleção vazia
Dado uma coleção vazia
Quando chamo search("qualquer coisa")
Então retorna []

# Search — score abaixo do mínimo
Dado chunks com score < min_score para a query
Quando chamo search(query, min_score=0.9)
Então nenhum chunk é retornado

# Métricas — role
Dado um usuário autenticado com role != "ADMIN"
Quando chamo GET /api/v1/admin/metrics/
Então retorna 403 FORBIDDEN
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Ingestão + retrieval (RF-01 a RF-06) | Must | Base do RAG que alimenta as respostas contextualizadas da IA |
| Métricas admin (RF-07) | Should | Painel operacional; não bloqueia o MVP funcional |
| Telemetria desativada (RF-08) | Should | Privacidade e estabilidade do ChromaDB; já implementado |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/rag/models.py:5-33` | `KnowledgeDocument` | 🟢 |
| `apps/rag/ingestion.py:16-70` | `ALLOWED_MIMETYPES`, `MAX_BYTES`, `_extract_text`, `_split`, `_get_embeddings`, `ingest` | 🟢 |
| `apps/rag/vector_store.py:11-34` | `COLLECTION_NAME`, `get_collection` (singleton thread-safe) | 🟢 |
| `apps/rag/retriever.py:10-52` | `_get_embeddings`, `search` | 🟢 |
| `apps/rag/views.py:23-131` | `upload`, `list_documents`, `document_status`, `metrics`, `delete_document` | 🟢 |
| `apps/rag/urls.py:10-15` | rotas de upload/list/status/delete da unit | 🟢 |
| `apps/audit/urls.py:8` | montagem de `metrics/` → `/api/v1/admin/metrics/` (fora do `knowledge/`) | 🟢 [Revisão Codex] |
| `config/urls.py:35` | montagem de `api/v1/admin/knowledge/` → rag.urls (sem `metrics/`) | 🟢 [Revisão Codex] |
| `apps/rag/telemetry_noop.py:8-14` | `NoopProductTelemetry.capture` | 🟢 |
| `apps/rag/migrations/0001_initial.py` | schema `KnowledgeDocument` | 🟢 |
| `apps/ai_engine/orchestrator.py:124-128` | consumidor: `search` no `_build_messages` | 🟡 |

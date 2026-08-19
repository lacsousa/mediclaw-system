# User Stories — Base de Conhecimento (RAG)

> Fluxo: upload/ingestão, retrieval, exclusão e singleton do vector store.
> Cobertura: módulo `rag`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## US-RAG-01 — Fazer upload e indexar documento

**Como** administrador,
**quero** enviar um PDF/Markdown/TXT de literatura científica,
**para** alimentar a base de conhecimento que fundamenta as respostas da IA.

- Critérios de aceite:
  - POST `/api/v1/admin/knowledge/upload/` (multipart `file` + `title` opcional) → 201 `{id, title, status, chunk_count}`.
  - Arquivo ausente → 400 `VALIDATION_ERROR`; > 10MB → 400 `FILE_TOO_LARGE`; MIME fora da lista → 400 `INVALID_FILE_TYPE`.
  - Ingestão síncrona: extração (pypdf/utf-8) → chunking (1000/200) → embeddings → `coll.add`.
  - Falha → `status=ERROR` com `error_message` truncado em 1000. 🟢

## US-RAG-02 — Recuperar evidências para a resposta

**Como** orquestrador da IA,
**quero** recuperar os chunks mais relevantes para a pergunta,
**para** fundamentar a resposta com citações da base.

- Critérios de aceite:
  - `search(query, k=RAG_TOP_K=5, min_score=RAG_MIN_SCORE=0.75)` → chunks ordenados por score desc.
  - Score = `max(0.0, 1.0 - dist/2.0)`; abaixo do limiar → descartado.
  - Coleção vazia → `[]`. 🟢 (🟡 default da assinatura é 0.40 — divergente do env)

## US-RAG-03 — Consultar e excluir documento

**Como** administrador,
**quero** ver o status dos documentos e excluir os desnecessários,
**para** manter a base curada.

- Critérios de aceite:
  - GET `/api/v1/admin/knowledge/` → lista; GET `/api/v1/admin/knowledge/<id>/status/` → `{id, status, chunk_count, error_message}`.
  - DELETE `/api/v1/admin/knowledge/<id>/` → 204 (remove chunks do ChromaDB + registro).
  - Documento em `PROCESSING` → 409 `CONFLICT`. 🟢
  - 🔴 Lacuna: busca por `pk` sem escopo ao uploader — qualquer autenticado deleta de terceiros.

## US-RAG-04 — Vector store único e persistente

**Como** sistema,
**quero** uma única coleção ChromaDB por processo com telemetria desativada,
**para** economizar recursos e evitar chamadas de telemetria para o vendor.

- Critérios de aceite:
  - `get_collection()` singleton thread-safe (double-checked locking), coleção `mediclaw_kb`, persistida em `CHROMA_PERSIST_DIR`.
  - `NoopProductTelemetry` + `ANONYMIZED_TELEMETRY=False`.
  - `CHROMA_PERSIST_DIR` ausente → erro claro (hoje `KeyError` cru — 🔴 lacuna). 🟢

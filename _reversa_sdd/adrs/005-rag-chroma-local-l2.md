# ADR-005 — RAG com ChromaDB local e retorno ao espaço L2

**Status:** Aceito (iterado) 🟢
**Data:** 2026-06-26 a 2026-06-27
**Fonte:** histórico Git — `9719557` (migração para cosine, collection `mediclaw_kb_v2`, threshold 0.40), `0f193a5` (retorno ao default `space='l2'`, collection `mediclaw_kb`, score `1 − dist/2`), estado atual de `apps/rag/`.

## Contexto

O MVP precisa de uma base de conhecimento (PDF/MD/TXT) indexada e recuperável para embasar as respostas do chat, com baixo custo de infraestrutura. Decisões de métrica de distância afetam a qualidade do retrieval.

## Decisão (estado atual)

- **Vector store:** ChromaDB **local** (`CHROMA_PERSIST_DIR`), collection `mediclaw_kb`, telemetria desativada.
- **Espaço:** default `space='l2'`; para vetores OpenAI normalizados, `cosine_sim = 1 − dist/2`; `score = max(0, 1 − dist/2)`.
- **Threshold:** filtro `score < min_score` descarta o chunk. Default da função `search()` = `0.40`; o orquestrador injeta `RAG_MIN_SCORE` do env (padrão `0.75`) e `RAG_TOP_K=5`.
- **Embeddings:** `text-embedding-3-small` (OpenAI, 1536 dim).
- **Chunking:** `RecursiveCharacterTextSplitter(1000/200)`.
- **Migração futura:** `pgvector` planejada pós-MVP (Epic 9, `0d6a52d`).

## Consequências

- Evolução: `v1 (l2)` → cosine em `mediclaw_kb_v2` (9719557) → **retorno ao default l2** com nome padronizado `mediclaw_kb` (0f193a5). O motivo do retorno ao L2 **não está documentado** nos commits. 🟡 INFERIDO (provável: evitar re-embedding/migração de dados ou diferença de qualidade em vetores OpenAI).
- **Divergência de threshold:** função default `0.40` vs env `0.75` — comportamento depende do chamador. 🟡
- Ingestão síncrona: upload de até 10 MB trava o request (sem fila/background).
- `min_score` alto (0.75) reduz falsos positivos, mas pode deixar o chat sem evidência para consultas específicas ("sem evidências específicas para esta consulta").

## Alternativas consideradas

- **Cosine** (9719557) — tentado e revertido para L2.
- **pgvector** — postergado para pós-MVP (multi-tenancy previsto no Epic 9).

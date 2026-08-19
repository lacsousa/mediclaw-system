# RAG / Retrieval, Design Técnico

> Contrato operacional de **COMO** o retrieval é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `search` | `(query: str, k: int = 5, min_score: float = 0.40) -> list[dict]` | chunks `{content, source, chunk_id, document_id, score}` (`retriever.py:19-52`) |

> ⚠️ Default da função é `min_score=0.40`, mas o orquestrador chama com `RAG_MIN_SCORE=0.75` — o default da assinatura diverge do contrato/env. 🟡

## Fluxo Principal

1. `coll = get_collection()`; se `coll.count() == 0` → `[]`. (`retriever.py:25-27`) 🟢
2. `qvec = _get_embeddings().embed_query(query)` — embeddings em cache singleton `_emb` (module-scope). (`retriever.py:7-16,29`) 🟢
3. `coll.query(query_embeddings=[qvec], n_results=min(k, coll.count()), include=["documents", "metadatas", "distances"])`. (`retriever.py:30-34`) 🟢
4. Para cada resultado, converte distância L² → score: `max(0.0, 1.0 - (dist / 2.0))`; descarta `score < min_score`. (`retriever.py:40-42`) 🟢
5. Monta `{content, source=title, chunk_id=chunk_index, document_id, score=round(score, 4)}`. (`retriever.py:43-51`) 🟢

## Fluxos Alternativos

- **[Coleção vazia]:** retorna `[]` (early return). 🟢
- **[Score abaixo do mínimo]:** chunk descartado (`continue`). 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.rag.services.vector_store.get_collection` | Coleção `mediclaw_kb` | `coll.count()`/`coll.query()` |
| `langchain_openai.OpenAIEmbeddings` | Query embedding | singleton `_emb` (`retriever.py:7`) |
| `apps.ai_engine.orchestrator` | Consumidor | injeta chunks no system prompt |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Conversão L² → score `max(0.0, 1.0 - dist/2.0)` | `retriever.py:22-23,40` | 🟡 (equivale a cosseno só com vetores normalizados; hipótese não fixada na coleção) [Revisão Codex] |
| Embeddings de query em singleton module-scope | `retriever.py:7-16` | 🟢 |
| `os.environ` para `EMBEDDING_MODEL` fora de `settings.py` | `retriever.py:14` | 🟢 |
| Default `min_score=0.40` diverge do env `RAG_MIN_SCORE=0.75` | `retriever.py:19` | 🟡 |

## Riscos e Lacunas

- 🟡 Divergência de `min_score`: chamadas sem o argumento usam 0.40, não 0.75.
- 🟢 Sem logs de sucesso/latência de recuperação — baixa observabilidade de qualidade do RAG.

import os

from langchain_openai import OpenAIEmbeddings

from .vector_store import get_collection

_emb = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _emb
    if _emb is None:
        _emb = OpenAIEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        )
    return _emb


def search(query: str, k: int = 5, min_score: float = 0.40) -> list[dict]:
    """
    Busca chunks relevantes no vector store.
    A coleção usa espaço cosseno: ChromaDB retorna distância cosseno em [0, 1]
    onde 0 = idêntico. Convertemos para score de similaridade: score = 1 - dist.
    """
    coll = get_collection()
    if coll.count() == 0:
        return []

    qvec = _get_embeddings().embed_query(query)
    res = coll.query(
        query_embeddings=[qvec],
        n_results=min(k, coll.count()),
        include=["documents", "metadatas", "distances"],
    )

    out = []
    for content, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        score = max(0.0, 1.0 - dist)
        if score < min_score:
            continue
        out.append(
            {
                "content": content,
                "source": meta.get("title", "desconhecida"),
                "chunk_id": str(meta.get("chunk_index", "")),
                "document_id": meta.get("document_id"),
                "score": round(score, 4),
            }
        )
    return out

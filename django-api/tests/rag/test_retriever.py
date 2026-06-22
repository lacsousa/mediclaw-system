import hashlib

import pytest

from apps.accounts.models import User


def _fake_embed(texts):
    result = []
    for t in texts:
        h = hashlib.md5(t.encode()).digest()
        vec = [(b / 255.0) for b in h] * 8  # 128 dims
        result.append(vec)
    return result


def _fake_embed_query(text):
    return _fake_embed([text])[0]


@pytest.fixture(autouse=True)
def chroma_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    import apps.rag.vector_store as vs

    monkeypatch.setattr(vs, "_client", None)
    monkeypatch.setattr(vs, "_collection", None)


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    from langchain_openai import OpenAIEmbeddings

    monkeypatch.setattr(
        OpenAIEmbeddings, "embed_documents", lambda self, texts: _fake_embed(texts)
    )
    monkeypatch.setattr(
        OpenAIEmbeddings, "embed_query", lambda self, text: _fake_embed_query(text)
    )
    import apps.rag.retriever as ret

    monkeypatch.setattr(ret, "_emb", None)


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        email="admin@example.com",
        password="Admin1234",
        role="ADMIN",
    )
    return u


def _index_text(text: str, title: str, admin_user, doc_id: int = 1):
    """Indexa texto diretamente no Chroma (bypassa DB)."""
    from apps.rag.ingestion import _get_embeddings, _split
    from apps.rag.vector_store import get_collection

    chunks = _split(text)
    vectors = _get_embeddings().embed_documents(chunks)
    coll = get_collection()
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": str(doc_id), "title": title, "chunk_index": i}
        for i in range(len(chunks))
    ]
    coll.add(ids=ids, documents=chunks, embeddings=vectors, metadatas=metadatas)


def test_search_empty_collection_returns_empty():
    from apps.rag.retriever import search

    result = search("qualquer coisa")
    assert result == []


def test_search_returns_chunk_after_indexing(admin_user):
    from apps.rag.retriever import search

    texto = "Exercício físico regular reduz o risco de doenças cardiovasculares."
    _index_text(texto, "Guia de Saúde", admin_user)

    # busca com a mesma query → embedding idêntico → score máximo
    results = search(texto, k=5, min_score=0.0)
    assert len(results) >= 1
    assert results[0]["source"] == "Guia de Saúde"
    assert "content" in results[0]
    assert "chunk_id" in results[0]
    assert "score" in results[0]


def test_search_filters_low_score(admin_user):
    from apps.rag.retriever import search

    texto = "Alimentação saudável inclui frutas e verduras."
    _index_text(texto, "Nutrição", admin_user, doc_id=2)

    # min_score=1.1 é impossível (score max=1.0) → sempre retorna []
    results = search(texto, k=5, min_score=1.1)
    assert results == []


def test_search_result_keys(admin_user):
    from apps.rag.retriever import search

    texto = "Hidratação adequada é essencial para a saúde."
    _index_text(texto, "Dicas", admin_user, doc_id=3)

    results = search(texto, k=1, min_score=0.0)
    assert len(results) >= 1
    keys = set(results[0].keys())
    assert {"content", "source", "chunk_id", "document_id", "score"}.issubset(keys)

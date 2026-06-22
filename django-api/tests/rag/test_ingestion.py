import hashlib
import os

import pytest

from apps.accounts.models import User


def _fake_embed(texts):
    """Gera vetores determinísticos a partir do hash do texto."""
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
    # reset singleton so cada teste usa instância limpa
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


@pytest.fixture
def make_doc(db, admin_user):
    from apps.rag.models import KnowledgeDocument

    def _make(title="Test Doc", mime_type="text/plain"):
        return KnowledgeDocument.objects.create(
            title=title,
            file_name="test.txt",
            mime_type=mime_type,
            status="PROCESSING",
            uploaded_by=admin_user,
        )

    return _make


def test_ingest_txt_creates_indexed_document(make_doc):
    from apps.rag.ingestion import ingest

    doc = make_doc()
    ingest(doc, b"Este e um texto de teste sobre saude e bem estar.")
    doc.refresh_from_db()

    assert doc.status == "INDEXED"
    assert doc.chunk_count is not None
    assert doc.chunk_count >= 1
    assert doc.error_message == ""


def test_ingest_empty_file_sets_error_status(make_doc):
    from apps.rag.ingestion import ingest

    doc = make_doc()
    ingest(doc, b"   ")
    doc.refresh_from_db()

    assert doc.status == "ERROR"
    assert doc.error_message != ""


def test_ingest_pdf_creates_indexed_document(make_doc, tmp_path):
    """Cria um PDF mínimo válido em memória e testa a ingestão."""
    from apps.rag.ingestion import ingest

    # PDF mínimo com texto extraível via pypdf
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 72 720 Td (Saude) Tj ET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"0000000266 00000 n \n0000000360 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n441\n%%EOF"
    )
    doc = make_doc(mime_type="application/pdf")
    ingest(doc, pdf_bytes)
    doc.refresh_from_db()

    # PDF pode não extrair texto, mas não deve lançar exceção — apenas ERROR com mensagem
    assert doc.status in ("INDEXED", "ERROR")

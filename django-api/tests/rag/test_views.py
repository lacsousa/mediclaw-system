import hashlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User


def _fake_embed(texts):
    result = []
    for t in texts:
        h = hashlib.md5(t.encode()).digest()
        vec = [(b / 255.0) for b in h] * 8
        result.append(vec)
    return result


@pytest.fixture(autouse=True)
def chroma_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    import apps.rag.vector_store as vs
    monkeypatch.setattr(vs, "_client", None)
    monkeypatch.setattr(vs, "_collection", None)


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    from langchain_openai import OpenAIEmbeddings
    monkeypatch.setattr(OpenAIEmbeddings, "embed_documents", lambda self, texts: _fake_embed(texts))
    monkeypatch.setattr(OpenAIEmbeddings, "embed_query", lambda self, text: _fake_embed([text])[0])
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
def regular_user(db):
    u = User.objects.create_user(
        email="user@example.com",
        password="User1234",
    )
    return u


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def user_client(regular_user):
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client


def _txt_file(content: str = "Saúde e bem estar.") -> SimpleUploadedFile:
    return SimpleUploadedFile("test.txt", content.encode(), content_type="text/plain")


def test_upload_txt_returns_indexed_status(admin_client):
    resp = admin_client.post(
        "/api/v1/admin/knowledge/upload/",
        {"file": _txt_file("Texto de teste sobre saúde."), "title": "Meu Doc"},
        format="multipart",
    )
    assert resp.status_code == 201
    assert resp.data["status"] == "INDEXED"
    assert resp.data["chunk_count"] >= 1


def test_upload_rejects_missing_file(admin_client):
    resp = admin_client.post("/api/v1/admin/knowledge/upload/", {}, format="multipart")
    assert resp.status_code == 400


def test_upload_rejects_oversize(admin_client, monkeypatch):
    monkeypatch.setattr("apps.rag.views.MAX_BYTES", 5)
    resp = admin_client.post(
        "/api/v1/admin/knowledge/upload/",
        {"file": _txt_file("arquivo grande")},
        format="multipart",
    )
    assert resp.status_code == 400


def test_upload_rejects_invalid_mimetype(admin_client):
    html_file = SimpleUploadedFile("page.html", b"<html></html>", content_type="text/html")
    resp = admin_client.post(
        "/api/v1/admin/knowledge/upload/",
        {"file": html_file},
        format="multipart",
    )
    assert resp.status_code == 400


def test_non_admin_can_upload(user_client):
    # A base de conhecimento é compartilhada: qualquer usuário autenticado pode curá-la.
    resp = user_client.post(
        "/api/v1/admin/knowledge/upload/",
        {"file": _txt_file()},
        format="multipart",
    )
    assert resp.status_code == 201
    assert resp.data["status"] == "INDEXED"


def test_anonymous_upload_returns_401(db):
    resp = APIClient().post(
        "/api/v1/admin/knowledge/upload/",
        {"file": _txt_file()},
        format="multipart",
    )
    assert resp.status_code == 401


def test_list_documents(admin_client):
    admin_client.post(
        "/api/v1/admin/knowledge/upload/",
        {"file": _txt_file(), "title": "Doc A"},
        format="multipart",
    )
    resp = admin_client.get("/api/v1/admin/knowledge/")
    assert resp.status_code == 200
    assert len(resp.data) >= 1


def test_delete_document_removes_from_chroma(admin_client):
    from apps.rag.models import KnowledgeDocument
    from apps.rag.vector_store import get_collection

    upload_resp = admin_client.post(
        "/api/v1/admin/knowledge/upload/",
        {"file": _txt_file("Texto que será deletado."), "title": "Para Deletar"},
        format="multipart",
    )
    doc_id = upload_resp.data["id"]
    before = get_collection().count()
    assert before > 0

    resp = admin_client.delete(f"/api/v1/admin/knowledge/{doc_id}/")
    assert resp.status_code == 204
    assert not KnowledgeDocument.objects.filter(pk=doc_id).exists()
    assert get_collection().count() == 0


def test_delete_processing_document_returns_409(admin_client, db, admin_user):
    from apps.rag.models import KnowledgeDocument

    doc = KnowledgeDocument.objects.create(
        title="Em Processo",
        file_name="proc.txt",
        mime_type="text/plain",
        status="PROCESSING",
        uploaded_by=admin_user,
    )
    resp = admin_client.delete(f"/api/v1/admin/knowledge/{doc.id}/")
    assert resp.status_code == 409

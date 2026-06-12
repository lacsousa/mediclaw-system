import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.conversations.models import Conversation, Message


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="Pass1234")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="other@example.com", password="Pass1234")


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def other_client(other_user):
    c = APIClient()
    c.force_authenticate(user=other_user)
    return c


@pytest.fixture
def conv(db, user):
    return Conversation.objects.create(doctor=user, title="Test")


# --- CRUD ---

def test_create_conversation(client):
    resp = client.post("/api/v1/conversations/")
    assert resp.status_code == 201
    assert "id" in resp.data
    assert "title" in resp.data
    assert "updated_at" in resp.data
    assert "patient" in resp.data
    assert resp.data["patient"] is None


def test_list_conversations_returns_own_only(client, other_client, user, other_user, db):
    Conversation.objects.create(doctor=user, title="Mine")
    Conversation.objects.create(doctor=other_user, title="Theirs")

    resp = client.get("/api/v1/conversations/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["title"] == "Mine"


def test_list_conversations_paginated(client, user, db):
    for i in range(5):
        Conversation.objects.create(doctor=user, title=f"Conv {i}")

    resp = client.get("/api/v1/conversations/?page=1")
    assert resp.status_code == 200
    assert resp.data["count"] == 5
    assert "results" in resp.data


def test_get_conversation_detail(client, conv):
    Message.objects.create(conversation=conv, role="USER", content="Olá")
    resp = client.get(f"/api/v1/conversations/{conv.id}/")
    assert resp.status_code == 200
    assert resp.data["conversation"]["id"] == conv.id
    assert len(resp.data["messages"]) == 1
    assert resp.data["messages"][0]["role"] == "USER"


def test_delete_conversation_soft_deletes(client, conv):
    resp = client.delete(f"/api/v1/conversations/{conv.id}/")
    assert resp.status_code == 204
    # Soft delete: não aparece na lista padrão
    assert not Conversation.objects.filter(pk=conv.id).exists()
    # Mas existe no all_objects
    assert Conversation.all_objects.filter(pk=conv.id).exists()
    assert Conversation.all_objects.get(pk=conv.id).deleted_at is not None


def test_other_user_cannot_access_conv(other_client, conv):
    # Ownership check via get(doctor=user) → 404 para outros usuários
    resp = other_client.delete(f"/api/v1/conversations/{conv.id}/")
    assert resp.status_code == 404


def test_get_nonexistent_conversation_returns_404(client):
    resp = client.get("/api/v1/conversations/99999/")
    assert resp.status_code == 404


def test_unauthenticated_returns_401(db):
    anon = APIClient()
    resp = anon.post("/api/v1/conversations/")
    assert resp.status_code == 401


# --- Stream ---

def test_stream_missing_token(conv):
    anon = APIClient()
    resp = anon.get(f"/api/v1/conversations/{conv.id}/stream/?prompt=Oi")
    assert resp.status_code == 401


def test_stream_empty_prompt(client, conv, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    token = str(RefreshToken.for_user(user).access_token)
    resp = client.get(f"/api/v1/conversations/{conv.id}/stream/?token={token}&prompt=")
    assert resp.status_code == 400


def test_stream_with_mock_orchestrator(db, user, conv, monkeypatch):
    from rest_framework_simplejwt.tokens import RefreshToken
    from apps.ai_engine import orchestrator

    def mock_stream(user_id, conv_id, prompt, **kwargs):
        yield {"type": "token", "content": "Olá"}
        yield {"type": "done", "tokens_used": 1, "blocked": False}

    monkeypatch.setattr(orchestrator, "generate_stream", mock_stream)

    token = str(RefreshToken.for_user(user).access_token)
    c = APIClient()
    resp = c.get(f"/api/v1/conversations/{conv.id}/stream/?token={token}&prompt=Oi")

    assert resp.status_code == 200
    assert resp["Content-Type"] == "text/event-stream"

    content = b"".join(resp.streaming_content).decode()
    assert '"type": "token"' in content
    assert '"type": "done"' in content

    assert Message.objects.filter(conversation=conv, role="ASSISTANT").exists()


@pytest.mark.django_db
def test_stream_second_prompt_includes_prior_assistant(db, user, conv, monkeypatch):
    """Segundo stream na mesma conversa deve enviar o turno anterior ao LLM."""
    from rest_framework_simplejwt.tokens import RefreshToken
    from apps.ai_engine import orchestrator

    Message.objects.create(conversation=conv, role="USER", content="Me chamo João")
    Message.objects.create(conversation=conv, role="ASSISTANT", content="Olá João!")

    class _RecordingProvider:
        last_messages = None

        def stream(self, messages, max_tokens):
            _RecordingProvider.last_messages = messages
            yield "Ok "

        def complete(self, messages, max_tokens):
            _RecordingProvider.last_messages = messages
            return "ok", 1

    monkeypatch.setattr(orchestrator, "get_provider", lambda: _RecordingProvider())
    monkeypatch.setattr("apps.rag.retriever.search", lambda *a, **k: [])

    token = str(RefreshToken.for_user(user).access_token)
    c = APIClient()
    resp = c.get(
        f"/api/v1/conversations/{conv.id}/stream/",
        {"token": token, "prompt": "Qual é meu nome?"},
    )
    assert resp.status_code == 200
    b"".join(resp.streaming_content)

    turns = [
        m for m in _RecordingProvider.last_messages if m["role"] != "system"
    ]
    assert {"role": "assistant", "content": "Olá João!"} in turns
    assert turns[-1]["role"] == "user"
    assert turns[-1]["content"] == "Qual é meu nome?"
    assert len([m for m in turns if m["role"] == "user"]) == 2

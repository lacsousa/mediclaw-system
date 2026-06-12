import pytest

from apps.accounts.models import User
from apps.conversations.models import Conversation, Message
from apps.conversations.services.welcome import (
    WELCOME_CONVERSATION_TITLE,
    WELCOME_MESSAGE,
    ensure_welcome_conversation,
)


@pytest.mark.django_db
class TestWelcomeConversation:
    def test_welcome_message_contains_instructions(self):
        assert "MediClaw" in WELCOME_MESSAGE
        assert "paciente" in WELCOME_MESSAGE.lower()

    def test_ensure_creates_conversation_and_assistant_message(self, user):
        conv = ensure_welcome_conversation(user)
        assert conv is not None
        assert conv.title == WELCOME_CONVERSATION_TITLE
        assert Message.objects.filter(conversation=conv, role="ASSISTANT").count() == 1
        msg = Message.objects.get(conversation=conv, role="ASSISTANT")
        assert msg.metadata.get("welcome") is True
        assert msg.tokens_used == 0

    def test_ensure_is_idempotent(self, user):
        first = ensure_welcome_conversation(user)
        second = ensure_welcome_conversation(user)
        assert first.id == second.id
        assert Conversation.objects.filter(doctor=user).count() == 1

    def test_admin_user_skips_welcome(self, db):
        admin = User.objects.create_user(
            email="admin@example.com",
            password="Pass1234",
            role="ADMIN",
        )
        assert ensure_welcome_conversation(admin) is None

    def test_register_creates_welcome_via_api(self, api_client):
        data = {
            "email": "welcome@example.com",
            "password": "ValidPassword123",
            "name": "Welcome User",
            "accept_terms": True,
        }
        resp = api_client.post("/api/v1/auth/register/", data=data, format="json")
        assert resp.status_code == 201
        user = User.objects.get(email="welcome@example.com")
        conv = Conversation.objects.get(doctor=user, title=WELCOME_CONVERSATION_TITLE)
        assert Message.objects.filter(conversation=conv, role="ASSISTANT").exists()

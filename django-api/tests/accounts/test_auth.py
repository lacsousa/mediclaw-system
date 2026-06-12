import pytest
from rest_framework import status
from apps.accounts.models import User


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_user_and_returns_tokens(self, api_client):
        data = {
            "email": "newuser@example.com",
            "password": "ValidPassword123",
            "name": "New User",
            "accept_terms": True,
        }
        response = api_client.post("/api/v1/auth/register/", data=data, format="json")
        assert response.status_code == 201
        assert len(response.data["access"]) > 0  # token is a valid string
        assert len(response.data["refresh"]) > 0  # token is a valid string
        assert response.data["user"]["email"] == "newuser@example.com"
        assert response.data["user"]["first_name"] == "New User"
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_creates_welcome_conversation(self, api_client):
        from apps.conversations.models import Conversation, Message
        from apps.conversations.services.welcome import WELCOME_CONVERSATION_TITLE

        data = {
            "email": "welcome2@example.com",
            "password": "ValidPassword123",
            "name": "Welcome User",
            "accept_terms": True,
        }
        api_client.post("/api/v1/auth/register/", data=data, format="json")
        user = User.objects.get(email="welcome2@example.com")
        conv = Conversation.objects.get(doctor=user, title=WELCOME_CONVERSATION_TITLE)
        assert Message.objects.filter(conversation=conv, role="ASSISTANT").exists()

    def test_register_rejects_weak_password(self, api_client):
        data = {
            "email": "user@example.com",
            "password": "weak",
            "name": "User",
            "accept_terms": True,
        }
        response = api_client.post("/api/v1/auth/register/", data=data, format="json")
        assert response.status_code == 400
        assert "password" in response.data["error"].get("message", "")

    def test_register_blocks_without_accept_terms(self, api_client):
        data = {
            "email": "user@example.com",
            "password": "ValidPassword123",
            "name": "User",
            "accept_terms": False,
        }
        response = api_client.post("/api/v1/auth/register/", data=data, format="json")
        assert response.status_code == 400
        assert "accept_terms" in response.data["error"].get("message", "")

    def test_register_blocks_duplicate_email(self, api_client, user):
        data = {
            "email": user.email,
            "password": "ValidPassword123",
            "name": "Another User",
            "accept_terms": True,
        }
        response = api_client.post("/api/v1/auth/register/", data=data, format="json")
        assert response.status_code == 400
        assert "email" in response.data["error"].get("message", "")


@pytest.mark.django_db
class TestLogin:
    def test_login_success_returns_tokens(self, api_client, user):
        data = {
            "email": user.email,
            "password": "TestPassword123",
        }
        response = api_client.post("/api/v1/auth/login/", data=data, format="json")
        assert response.status_code == 200
        assert len(response.data["access"]) > 0
        assert len(response.data["refresh"]) > 0
        assert response.data["user"]["email"] == user.email

    def test_login_with_wrong_password_returns_401(self, api_client, user):
        data = {
            "email": user.email,
            "password": "WrongPassword",
        }
        response = api_client.post("/api/v1/auth/login/", data=data)
        assert response.status_code == 401
        assert response.data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_inactive_user_returns_401(self, api_client, user):
        user.is_active = False
        user.save()
        data = {
            "email": user.email,
            "password": "TestPassword123",
        }
        response = api_client.post("/api/v1/auth/login/", data=data)
        assert response.status_code == 401


@pytest.mark.django_db
class TestMe:
    def test_me_requires_auth(self, api_client):
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == 401

    def test_me_get_returns_user_data(self, auth_client, user):
        response = auth_client.get("/api/v1/auth/me/")
        assert response.status_code == 200
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name

    def test_me_patch_updates_name(self, auth_client, user):
        data = {"name": "Updated Name"}
        response = auth_client.patch("/api/v1/auth/me/", data=data)
        assert response.status_code == 200
        assert response.data["first_name"] == "Updated Name"
        user.refresh_from_db()
        assert user.first_name == "Updated Name"

    def test_me_patch_rejects_duplicate_email(self, api_client, user):
        other = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123",
            first_name="Other",
        )
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            "/api/v1/auth/me/",
            data={"email": other.email},
            format="json",
        )
        assert response.status_code == 400
        assert "email" in response.data["error"].get("message", "")

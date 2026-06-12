# Epic 6 — Conversations & Chat

> **Plano-MVP Etapas 2 + 5 (lado backend).** CRUD de conversas, envio de mensagens e streaming SSE.
> Referência: [PRD §EPIC-06](../PRD.md) · [TASKS §Epic 6](../TASKS.md#epic-6--conversations--chat)

---

## Objetivo

Expor o chat persistido com a IA: criar/listar/excluir conversas, enviar mensagem (com resposta gerada via orquestrador) e oferecer streaming SSE para o cliente.

## Dependências

- E2 (auth), E4 (ai_engine), E5 (rag)

---

## Modelos

```python
# apps/conversations/models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["user", "-updated_at"])]
        ordering = ["-updated_at"]


class Message(models.Model):
    ROLE_CHOICES = [("USER","USER"),("ASSISTANT","ASSISTANT"),("SYSTEM","SYSTEM")]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    blocked_by_guardrail = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [models.Index(fields=["conversation", "created_at"])]
        ordering = ["created_at"]
```

---

## Serializers

```python
# apps/conversations/serializers.py
from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "tokens_used", "blocked_by_guardrail", "metadata", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at"]


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ["messages"]


class CreateMessageInput(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=4000)
```

---

## Service de Chat

```python
# apps/conversations/services/chat.py
import os
from django.db import transaction
from apps.common.exceptions import AppError
from apps.ai_engine.orchestrator import generate
from ..models import Conversation, Message

MAX_MESSAGES = int(os.environ.get("MAX_MESSAGES_PER_CONVERSATION", "50"))


def send_message(user, conversation: Conversation, content: str) -> Message:
    if conversation.user_id != user.id:
        raise AppError("FORBIDDEN", "Conversa não pertence ao usuário.", 403)
    if conversation.messages.count() >= MAX_MESSAGES:
        raise AppError("CONVERSATION_LIMIT_REACHED", "Limite de mensagens atingido.", 400)

    with transaction.atomic():
        Message.objects.create(conversation=conversation, role="USER", content=content)

    result = generate(user.id, conversation.id, content)
    citations = [{"source": c["source"], "chunk_id": c.get("chunk_id")} for c in (result.citations or [])]
    assistant_msg = Message.objects.create(
        conversation=conversation,
        role="ASSISTANT",
        content=result.content,
        tokens_used=result.tokens_used,
        blocked_by_guardrail=result.blocked_by_guardrail,
        metadata={"citations": citations},
    )
    conversation.save(update_fields=["updated_at"])
    return assistant_msg
```

---

## Views

```python
# apps/conversations/views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer, ConversationDetailSerializer,
    MessageSerializer, CreateMessageInput,
)
from .services.chat import send_message


class ChatThrottle(UserRateThrottle):
    scope = "chat"


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="messages", throttle_classes=[ChatThrottle])
    def post_message(self, request, pk=None):
        conv = self.get_object()
        s = CreateMessageInput(data=request.data)
        s.is_valid(raise_exception=True)
        msg = send_message(request.user, conv, s.validated_data["content"])
        return Response(MessageSerializer(msg).data, status=201)
```

---

## Streaming SSE

```python
# apps/conversations/sse.py
import json, asyncio
from urllib.parse import unquote
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import aget_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from apps.ai_engine.orchestrator import generate_stream

User = get_user_model()


async def _resolve_user(token: str):
    try:
        payload = AccessToken(token)
        user = await User.objects.aget(pk=payload["user_id"])
        return user if user.is_active else None
    except Exception:
        return None


async def stream_view(request, conv_id: int):
    token = request.GET.get("token") or (
        request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    )
    user = await _resolve_user(token)
    if not user:
        return JsonResponse({"data": None, "error": {"code": "INVALID_TOKEN", "message": "Token inválido."}, "meta": {}}, status=401)

    prompt = unquote(request.GET.get("prompt") or "")
    if not prompt:
        return JsonResponse({"data": None, "error": {"code": "VALIDATION_ERROR", "message": "prompt obrigatório"}, "meta": {}}, status=400)

    conv = await aget_object_or_404(Conversation, pk=conv_id, user=user)

    async def gen():
        # persiste a mensagem do usuário antes de iniciar o stream
        await Message.objects.acreate(conversation=conv, role="USER", content=prompt)
        full = []
        citations_collected = []
        blocked = False
        tokens_used = 0
        try:
            for event in generate_stream(user.id, conv.id, prompt):
                if event["type"] == "token":
                    full.append(event["content"])
                if event["type"] == "citation":
                    citations_collected.append({"source": event.get("source"), "chunk_id": event.get("chunk_id")})
                if event["type"] == "done":
                    blocked = event.get("blocked", False)
                    tokens_used = event.get("tokens_used", 0)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)
        finally:
            content = "".join(full).strip()
            if content:
                await Message.objects.acreate(
                    conversation=conv, role="ASSISTANT", content=content,
                    tokens_used=tokens_used, blocked_by_guardrail=blocked,
                    metadata={"citations": citations_collected},
                )

    response = StreamingHttpResponse(gen(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
```

```python
# apps/conversations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet
from .sse import stream_view

router = DefaultRouter()
router.register("", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("<int:conv_id>/stream", stream_view),
    path("", include(router.urls)),
]
```

> Em produção rodar com `uvicorn config.asgi:application` para que SSE funcione corretamente. Em dev `runserver` aceita ASGI views via `ASGI_APPLICATION`.

---

## Critérios de Aceite

- [ ] CRUD de conversas restrito ao próprio usuário
- [ ] `POST /api/v1/conversations/{id}/messages` salva user + assistant atomicamente
- [ ] Conversa com 50 mensagens → 400 `CONVERSATION_LIMIT_REACHED`
- [ ] `content` vazio ou > 4000 chars → 400 `VALIDATION_ERROR`
- [ ] SSE: token, citation, done com payloads conforme PRD
- [ ] SSE persiste a mensagem completa do assistente mesmo se cliente desconectar
- [ ] Throttle `chat=10/min` ativo no envio
- [ ] Erro do provedor LLM → 502 `LLM_PROVIDER_ERROR`; mensagem do usuário fica salva, mensagem da IA não é criada

---

## Testes obrigatórios

```python
# tests/conversations/test_crud.py
def test_user_only_lists_own_conversations(): ...
def test_delete_other_users_conversation_returns_403(): ...

# tests/conversations/test_send_message.py
def test_send_message_persists_user_and_assistant(monkeypatch): ...
def test_send_message_blocked_message_keeps_blocked_flag(monkeypatch): ...
def test_send_message_over_limit_returns_400(): ...
def test_provider_error_keeps_user_message(monkeypatch): ...

# tests/conversations/test_stream.py
def test_stream_yields_done_event(async_client, monkeypatch): ...
def test_stream_persists_assistant_message_on_completion(async_client, monkeypatch): ...
def test_stream_requires_valid_token(async_client): ...
```

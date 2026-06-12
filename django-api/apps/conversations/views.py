import json
import logging

from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.common.exceptions import AppError

from .models import Conversation, Message
from .serializers import MessageSerializer, CreateMessageInput
from .services.chat import send_message

logger = logging.getLogger(__name__)

PAGE_SIZE = 20
MAX_MESSAGES = 50


class ChatThrottle(UserRateThrottle):
    scope = "chat"


def _serialize_patient(patient) -> dict | None:
    if patient is None:
        return None
    return {"id": patient.id, "first_name": patient.first_name}


def _serialize_conversation(conv: Conversation) -> dict:
    return {
        "id": conv.id,
        "title": conv.title,
        "patient": _serialize_patient(conv.patient),
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


def _serialize_message(msg: Message) -> dict:
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "tokens_used": msg.tokens_used,
        "blocked_by_guardrail": msg.blocked_by_guardrail,
        "metadata": msg.metadata,
        "created_at": msg.created_at.isoformat(),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_create(request):
    if request.method == "POST":
        conv = Conversation.objects.create(doctor=request.user, title="Nova conversa")
        return Response(_serialize_conversation(conv), status=201)

    page = int(request.GET.get("page", 1))
    offset = (page - 1) * PAGE_SIZE
    qs = Conversation.objects.filter(doctor=request.user).select_related("patient")
    total = qs.count()
    items = qs[offset: offset + PAGE_SIZE]
    has_next = offset + PAGE_SIZE < total
    return Response(
        {
            "results": [_serialize_conversation(c) for c in items],
            "count": total,
            "next": f"?page={page + 1}" if has_next else None,
        }
    )


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def detail(request, conv_id: int):
    try:
        conv = Conversation.objects.select_related("patient").get(
            pk=conv_id, doctor=request.user
        )
    except Conversation.DoesNotExist:
        raise AppError("NOT_FOUND", "Conversa não encontrada.", 404)

    if request.method == "DELETE":
        conv.deleted_at = timezone.now()
        conv.save(update_fields=["deleted_at"])
        return Response(status=204)

    messages = conv.messages.all()
    return Response(
        {
            "conversation": _serialize_conversation(conv),
            "messages": [_serialize_message(m) for m in messages],
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ChatThrottle])
def post_message(request, conv_id: int):
    """POST /api/v1/conversations/{id}/messages/ - Enviar mensagem."""
    try:
        conv = Conversation.objects.get(pk=conv_id, doctor=request.user)
    except Conversation.DoesNotExist:
        raise AppError("NOT_FOUND", "Conversa não encontrada.", 404)

    s = CreateMessageInput(data=request.data)
    s.is_valid(raise_exception=True)

    msg = send_message(request.user, conv, s.validated_data["content"])
    return Response(MessageSerializer(msg).data, status=201)


def stream(request, conv_id: int):
    """GET /api/v1/conversations/{id}/stream/ — auth via ?token= (EventSource sem headers)."""
    token_str = request.GET.get("token", "")
    prompt = (request.GET.get("prompt") or "").strip()

    if not token_str:
        return StreamingHttpResponse(
            iter([f'data: {json.dumps({"type": "error", "code": "UNAUTHORIZED", "message": "Token ausente."})}\n\n']),
            content_type="text/event-stream",
            status=401,
        )

    try:
        token = AccessToken(token_str)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=token["user_id"])
    except (TokenError, Exception):
        return StreamingHttpResponse(
            iter([f'data: {json.dumps({"type": "error", "code": "UNAUTHORIZED", "message": "Token inválido."})}\n\n']),
            content_type="text/event-stream",
            status=401,
        )

    try:
        conv = Conversation.objects.get(pk=conv_id, doctor=user)
    except Conversation.DoesNotExist:
        return StreamingHttpResponse(
            iter([f'data: {json.dumps({"type": "error", "code": "NOT_FOUND", "message": "Conversa não encontrada."})}\n\n']),
            content_type="text/event-stream",
            status=404,
        )

    if not prompt:
        return StreamingHttpResponse(
            iter([f'data: {json.dumps({"type": "error", "code": "VALIDATION_ERROR", "message": "Prompt vazio."})}\n\n']),
            content_type="text/event-stream",
            status=400,
        )

    if conv.messages.count() >= MAX_MESSAGES:
        return StreamingHttpResponse(
            iter([f'data: {json.dumps({"type": "error", "code": "CONVERSATION_FULL", "message": "Limite de mensagens atingido."})}\n\n']),
            content_type="text/event-stream",
            status=400,
        )

    is_first = conv.messages.count() == 0
    Message.objects.create(conversation=conv, role="USER", content=prompt)
    if not conv.title or conv.title == "Nova conversa":
        conv.title = prompt[:80]
        conv.save(update_fields=["title", "updated_at"])

    def event_stream():
        from apps.ai_engine.orchestrator import generate_stream

        full_content: list[str] = []
        citations: list[dict] = []
        tokens_used = 0
        blocked = False
        onboarding_mode = None
        missing_basics = None
        data_capture = None
        patient_id = None
        patient_created = False
        patient_first_name = None

        try:
            for event in generate_stream(
                user.id, conv.id, prompt, is_first_message=is_first
            ):
                if event["type"] == "token":
                    full_content.append(event.get("content", ""))
                elif event["type"] == "citation":
                    citations.append({"source": event.get("source"), "chunk_id": event.get("chunk_id")})
                elif event["type"] == "done":
                    tokens_used = event.get("tokens_used", 0)
                    blocked = event.get("blocked", False)
                    onboarding_mode = event.get("onboarding_mode")
                    missing_basics = event.get("missing_basics")
                    data_capture = event.get("data_capture")
                    patient_id = event.get("patient_id")
                    patient_created = event.get("patient_created", False)
                    patient_first_name = event.get("patient_first_name")
                    metadata: dict = {"citations": citations}
                    if onboarding_mode:
                        metadata["onboarding_mode"] = onboarding_mode
                    if missing_basics:
                        metadata["missing_basics"] = missing_basics
                    if data_capture:
                        metadata["data_capture"] = data_capture
                    Message.objects.create(
                        conversation=conv,
                        role="ASSISTANT",
                        content="".join(full_content),
                        tokens_used=tokens_used,
                        blocked_by_guardrail=blocked,
                        metadata=metadata,
                    )
                    conv.save(update_fields=["updated_at"])
                elif event["type"] == "error":
                    logger.warning("Stream error for conv %s: %s", conv.id, event)

                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.exception("Unexpected error in stream for conv %s", conv.id)
            yield f'data: {json.dumps({"type": "error", "code": "INTERNAL_ERROR", "message": str(e)})}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

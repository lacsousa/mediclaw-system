import os
from django.db import transaction
from apps.common.exceptions import AppError
from apps.ai_engine import orchestrator
from ..models import Conversation, Message

MAX_MESSAGES = int(os.environ.get("MAX_MESSAGES_PER_CONVERSATION", "50"))


def send_message(user, conversation: Conversation, content: str) -> Message:
    if conversation.doctor_id != user.id:
        raise AppError("FORBIDDEN", "Conversa não pertence ao usuário.", 403)
    if conversation.messages.count() >= MAX_MESSAGES:
        raise AppError("CONVERSATION_FULL", "Limite de mensagens atingido.", 400)

    is_first = conversation.messages.count() == 0

    with transaction.atomic():
        Message.objects.create(conversation=conversation, role="USER", content=content)

    result = orchestrator.generate(
        user.id, conversation.id, content, is_first_message=is_first
    )
    citations = [
        {"source": c["source"], "chunk_id": c.get("chunk_id")}
        for c in (result.citations or [])
    ]
    metadata: dict = {"citations": citations}
    if result.onboarding_mode:
        metadata["onboarding_mode"] = result.onboarding_mode
    if result.missing_basics:
        metadata["missing_basics"] = result.missing_basics
    data_capture = getattr(result, "data_capture", None)
    if data_capture:
        metadata["data_capture"] = data_capture
    assistant_msg = Message.objects.create(
        conversation=conversation,
        role="ASSISTANT",
        content=result.content,
        tokens_used=result.tokens_used,
        blocked_by_guardrail=result.blocked_by_guardrail,
        metadata=metadata,
    )
    conversation.save(update_fields=["updated_at"])
    return assistant_msg

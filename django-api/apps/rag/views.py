from datetime import date

from django.db.models import Sum

from apps.accounts.models import User
from apps.conversations.models import Conversation, Message

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.services.log import record
from apps.common.exceptions import AppError
from apps.common.permissions import IsAdminRole

from .ingestion import ALLOWED_MIMETYPES, MAX_BYTES, ingest
from .models import KnowledgeDocument
from .vector_store import get_collection


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload(request):
    f = request.FILES.get("file")
    if not f:
        raise AppError("VALIDATION_ERROR", "Arquivo ausente.", 400)
    if f.size > MAX_BYTES:
        raise AppError("FILE_TOO_LARGE", "Arquivo excede 10 MB.", 400)
    if f.content_type not in ALLOWED_MIMETYPES:
        raise AppError(
            "INVALID_FILE_TYPE", f"Tipo não suportado: {f.content_type}", 400
        )

    title = (request.data.get("title") or f.name)[:200]
    doc = KnowledgeDocument.objects.create(
        title=title,
        file_name=f.name[:255],
        mime_type=f.content_type,
        status="PROCESSING",
        uploaded_by=request.user,
    )
    ingest(doc, f.read())
    record(
        "KB_UPLOAD",
        user=request.user,
        metadata={"document_id": doc.id, "status": doc.status},
    )
    return Response(
        {
            "id": doc.id,
            "title": doc.title,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
        },
        status=201,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_documents(request):
    qs = KnowledgeDocument.objects.values(
        "id", "title", "status", "chunk_count", "created_at"
    )
    return Response(list(qs))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_status(request, doc_id: int):
    try:
        doc = KnowledgeDocument.objects.get(pk=doc_id)
    except KnowledgeDocument.DoesNotExist:
        raise AppError("NOT_FOUND", "Documento não encontrado.", 404)
    return Response(
        {
            "id": doc.id,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "error_message": doc.error_message,
        }
    )


@api_view(["GET"])
@permission_classes([IsAdminRole])
def metrics(request):
    today = date.today()

    tokens = (
        Message.objects.filter(created_at__date=today)
        .aggregate(total=Sum("tokens_used"))
        .get("total")
        or 0
    )

    data = {
        "users_total": User.objects.count(),
        "conversations_total": Conversation.objects.count(),
        "messages_today": Message.objects.filter(created_at__date=today).count(),
        "tokens_today": tokens,
        "guardrail_blocks_today": Message.objects.filter(
            created_at__date=today,
            blocked_by_guardrail=True,
        ).count(),
        "kb_documents_indexed": KnowledgeDocument.objects.filter(
            status="INDEXED"
        ).count(),
    }

    return Response(data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(request, doc_id: int):
    try:
        doc = KnowledgeDocument.objects.get(pk=doc_id)
    except KnowledgeDocument.DoesNotExist:
        raise AppError("NOT_FOUND", "Documento não encontrado.", 404)
    if doc.status == "PROCESSING":
        raise AppError("CONFLICT", "Documento em processamento; aguarde concluir.", 409)

    coll = get_collection()
    coll.delete(where={"document_id": str(doc.id)})
    doc.delete()
    record("KB_DELETE", user=request.user, metadata={"document_id": doc_id})
    return Response(status=status.HTTP_204_NO_CONTENT)

# Epic 5 — RAG (Retrieval-Augmented Generation)

> **Plano-MVP Etapa 4.** Ingestão e recuperação semântica em literatura científica via ChromaDB.
> Referência: [PRD §EPIC-05](../PRD.md) · [TASKS §Epic 5](../TASKS.md#epic-5--rag)

---

## Objetivo

Permitir que o admin alimente uma base de conhecimento (PDF/MD/TXT) e que o orquestrador recupere chunks relevantes para fundamentar as respostas da IA.

## Dependências

- E1 (foundation), E2 (auth/admin), E4 (ai_engine — usa `retriever.search`)

> **Ordem prática:** E5 pode ser desenvolvido em paralelo com E4 desde que a interface `retriever.search()` esteja definida.

---

## Vector Store

```python
# apps/rag/vector_store.py
import os, threading
import chromadb
from chromadb.config import Settings

_lock = threading.Lock()
_client = None
_collection = None

COLLECTION_NAME = "mediclaw_kb"

def get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    with _lock:
        if _collection is not None:
            return _collection
        persist = os.environ["CHROMA_PERSIST_DIR"]
        os.makedirs(persist, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist, settings=Settings(anonymized_telemetry=False))
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
        return _collection
```

> ChromaDB persiste no diretório configurado (`CHROMA_PERSIST_DIR=/app/chroma_data` em prod). O volume Docker garante durabilidade entre restarts.

---

## Modelo

```python
# apps/rag/models.py
from django.db import models
from django.conf import settings

class KnowledgeDocument(models.Model):
    STATUS = [("PROCESSING","PROCESSING"),("INDEXED","INDEXED"),("ERROR","ERROR")]
    title = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=80)
    status = models.CharField(max_length=12, choices=STATUS, default="PROCESSING")
    chunk_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
```

---

## Pipeline de Ingestão

```python
# apps/rag/ingestion.py
import os, uuid, logging
from io import BytesIO
from typing import Iterable
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from .vector_store import get_collection
from .models import KnowledgeDocument

logger = logging.getLogger(__name__)

ALLOWED_MIMETYPES = {"application/pdf", "text/markdown", "text/plain"}
MAX_BYTES = 10 * 1024 * 1024


def _extract_text(file_bytes: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_bytes.decode("utf-8", errors="replace")


def _split(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(text)


def _embeddings():
    return OpenAIEmbeddings(model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))


def ingest(document: KnowledgeDocument, file_bytes: bytes) -> None:
    try:
        text = _extract_text(file_bytes, document.mime_type)
        if not text.strip():
            raise ValueError("Documento vazio ou sem texto extraível.")
        chunks = _split(text)
        emb = _embeddings()
        vectors = emb.embed_documents(chunks)

        coll = get_collection()
        ids = [f"{document.id}-{i}-{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": str(document.id), "title": document.title, "chunk_index": i}
            for i in range(len(chunks))
        ]
        coll.add(ids=ids, documents=chunks, embeddings=vectors, metadatas=metadatas)

        document.status = "INDEXED"
        document.chunk_count = len(chunks)
        document.error_message = ""
        document.save(update_fields=["status", "chunk_count", "error_message", "updated_at"])
    except Exception as e:
        logger.exception("Falha ao indexar documento %s", document.id)
        document.status = "ERROR"
        document.error_message = str(e)[:1000]
        document.save(update_fields=["status", "error_message", "updated_at"])
```

---

## Retriever

```python
# apps/rag/retriever.py
import os
from langchain_openai import OpenAIEmbeddings
from .vector_store import get_collection

_emb = None

def _get_embeddings():
    global _emb
    if _emb is None:
        _emb = OpenAIEmbeddings(model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))
    return _emb


def search(query: str, k: int = 5, min_score: float = 0.75) -> list[dict]:
    """
    Retorna lista de chunks com score normalizado [0,1].
    ChromaDB retorna 'distances' (cosine distance ∈ [0,2]); convertemos para similaridade = 1 - dist/2.
    """
    coll = get_collection()
    if coll.count() == 0:
        return []
    qvec = _get_embeddings().embed_query(query)
    res = coll.query(query_embeddings=[qvec], n_results=k, include=["documents", "metadatas", "distances"])
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    out = []
    for content, meta, dist in zip(docs, metas, dists):
        score = max(0.0, 1.0 - (dist / 2.0))
        if score < min_score:
            continue
        out.append({
            "content": content,
            "source": meta.get("title", "desconhecida"),
            "chunk_id": str(meta.get("chunk_index", "")),
            "document_id": meta.get("document_id"),
            "score": round(score, 4),
        })
    return out
```

> A relação `score = 1 - dist/2` assume distância cosseno do Chroma. Confirmar nos testes (`test_retriever_score_thresholding`).

---

## Endpoints (Admin)

```python
# apps/rag/views.py
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from apps.common.permissions import IsAdminRole
from apps.common.exceptions import AppError
from apps.audit.services.log import record
from .models import KnowledgeDocument
from .ingestion import ALLOWED_MIMETYPES, MAX_BYTES, ingest
from .vector_store import get_collection


@api_view(["POST"])
@permission_classes([IsAdminRole])
@parser_classes([MultiPartParser])
def upload(request):
    f = request.FILES.get("file")
    title = request.data.get("title") or (f.name if f else "")
    if not f:
        raise AppError("VALIDATION_ERROR", "Arquivo ausente.", 400)
    if f.size > MAX_BYTES:
        raise AppError("FILE_TOO_LARGE", "Arquivo excede 10MB.", 400)
    if f.content_type not in ALLOWED_MIMETYPES:
        raise AppError("INVALID_FILE_TYPE", f"Tipo não suportado: {f.content_type}", 400)
    doc = KnowledgeDocument.objects.create(
        title=title[:200], file_name=f.name[:255], mime_type=f.content_type,
        status="PROCESSING", uploaded_by=request.user,
    )
    ingest(doc, f.read())  # síncrono no MVP
    record("KB_UPLOAD", user=request.user, metadata={"document_id": doc.id, "status": doc.status})
    return Response({
        "id": doc.id, "title": doc.title, "status": doc.status, "chunk_count": doc.chunk_count
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAdminRole])
def list_documents(request):
    qs = KnowledgeDocument.objects.all().values(
        "id", "title", "status", "chunk_count", "created_at"
    )
    return Response(list(qs))


@api_view(["GET"])
@permission_classes([IsAdminRole])
def status_document(request, doc_id: int):
    try:
        doc = KnowledgeDocument.objects.get(pk=doc_id)
    except KnowledgeDocument.DoesNotExist:
        raise AppError("NOT_FOUND", "Documento não encontrado.", 404)
    return Response({"id": doc.id, "status": doc.status, "chunk_count": doc.chunk_count, "error_message": doc.error_message})


@api_view(["DELETE"])
@permission_classes([IsAdminRole])
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
    return Response(status=204)
```

```python
# apps/rag/urls.py
from django.urls import path
from .views import upload, list_documents, status_document, delete_document

urlpatterns = [
    path("upload", upload),
    path("", list_documents),
    path("<int:doc_id>/status", status_document),
    path("<int:doc_id>", delete_document),
]
```

---

## Healthcheck

```python
# apps/common/views.py — adicionar verificação de Chroma
from apps.rag.vector_store import get_collection

def _vector_ok():
    try:
        get_collection().count()
        return True
    except Exception:
        return False
```

---

## Critérios de Aceite

- [ ] Upload PDF/MD/TXT funciona e gera `KnowledgeDocument` com `status=INDEXED` quando ok
- [ ] Tamanho/tipo inválido → 400 com codes apropriados
- [ ] `retriever.search()` filtra score < 0.75 e retorna lista vazia quando não há matches
- [ ] DELETE de doc indexado remove chunks correspondentes do Chroma
- [ ] DELETE em doc `PROCESSING` retorna 409
- [ ] Healthcheck inclui `vector_store: ok`

---

## Testes obrigatórios

```python
# tests/rag/test_ingestion.py
def test_ingest_pdf_creates_indexed_document(): ...
def test_ingest_handles_extraction_error_sets_error_status(): ...
def test_upload_rejects_oversize(): ...
def test_upload_rejects_invalid_mimetype(): ...

# tests/rag/test_retriever.py
def test_search_returns_relevant_chunks_after_indexing(): ...
def test_search_filters_low_score(): ...
def test_search_empty_collection_returns_empty(): ...
```

> **Dica para testes:** usar `CHROMA_PERSIST_DIR=tmpdir` por teste para isolar coleções; mockar `OpenAIEmbeddings` com vetores determinísticos por hash do texto.

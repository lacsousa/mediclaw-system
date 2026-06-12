import logging
import os
import uuid
from io import BytesIO

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .models import KnowledgeDocument
from .vector_store import get_collection

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


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    )


def ingest(document: KnowledgeDocument, file_bytes: bytes) -> None:
    try:
        text = _extract_text(file_bytes, document.mime_type)
        if not text.strip():
            raise ValueError("Documento vazio ou sem texto extraível.")

        chunks = _split(text)
        vectors = _get_embeddings().embed_documents(chunks)

        coll = get_collection()
        ids = [f"{document.id}-{i}-{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": str(document.id),
                "title": document.title,
                "chunk_index": i,
            }
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

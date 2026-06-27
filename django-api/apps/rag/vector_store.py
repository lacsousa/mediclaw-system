import os
import threading

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import EmbeddingFunction

_lock = threading.Lock()
_client = None
_collection = None

COLLECTION_NAME = "mediclaw_kb_v2"  # v2 usa cosine; a v1 (l2) é mantida para não apagar dados existentes


def get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    with _lock:
        if _collection is not None:
            return _collection
        persist = os.environ["CHROMA_PERSIST_DIR"]
        os.makedirs(persist, exist_ok=True)
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
        _client = chromadb.PersistentClient(
            path=persist,
            settings=Settings(
                anonymized_telemetry=False,
                chroma_product_telemetry_impl=(
                    "apps.rag.telemetry_noop.NoopProductTelemetry"
                ),
            ),
        )
        _collection = _client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return _collection

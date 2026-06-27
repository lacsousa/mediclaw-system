import os
import threading

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
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
        return _collection

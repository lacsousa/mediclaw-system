"""
Script de migração: copia embeddings de mediclaw_kb (l2) → mediclaw_kb_v2 (cosine).
Execute com: python migrate_collection.py
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Lê CHROMA_PERSIST_DIR do .env manualmente (sem depender do Django carregado)
from pathlib import Path
env_file = Path(__file__).parent / ".env"
for line in env_file.read_text().splitlines():
    if line.startswith("CHROMA_PERSIST_DIR="):
        os.environ["CHROMA_PERSIST_DIR"] = line.split("=", 1)[1].strip()
        break

import chromadb
from chromadb.config import Settings

persist = os.environ["CHROMA_PERSIST_DIR"]
client = chromadb.PersistentClient(
    path=persist,
    settings=Settings(anonymized_telemetry=False),
)

src = client.get_collection("mediclaw_kb")
dst = client.get_or_create_collection("mediclaw_kb_v2", metadata={"hnsw:space": "cosine"})

total = src.count()
print(f"Migrando {total} embeddings de mediclaw_kb → mediclaw_kb_v2 ...")

BATCH = 500
offset = 0
migrated = 0

while offset < total:
    result = src.get(
        limit=BATCH,
        offset=offset,
        include=["documents", "metadatas", "embeddings"],
    )
    ids = result["ids"]
    if not ids:
        break

    dst.add(
        ids=ids,
        documents=result["documents"],
        metadatas=result["metadatas"],
        embeddings=result["embeddings"],
    )
    migrated += len(ids)
    print(f"  {migrated}/{total} chunks migrados")
    offset += BATCH

print(f"Concluído. Total na nova coleção: {dst.count()}")

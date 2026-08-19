# RAG / Collection Singleton, Design Técnico

> Contrato operacional de **COMO** o singleton do vector store é construído, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `get_collection` | `() -> Collection` | coleção ChromaDB `mediclaw_kb` (`vector_store.py:14-34`) |
| `NoopProductTelemetry.capture` | `(event: ProductTelemetryEvent) -> None` | no-op (`telemetry_noop.py:8-14`) |

## Fluxo Principal

1. `_collection` já setada → retorna direto. (`vector_store.py:16-17`) 🟢
2. Adquire `_lock`; **re-check** `_collection` (double-checked locking). (`vector_store.py:18-21`) 🟢
3. `CHROMA_PERSIST_DIR = os.environ["CHROMA_PERSIST_DIR"]`; `makedirs(..., exist_ok=True)`. (`vector_store.py:21-22`) 🟢
4. `ANONYMIZED_TELEMETRY` `setdefault` `False`; instancia `PersistentClient(path=..., settings=Settings(anonymized_telemetry=False, product_telemetry=...))`. (`vector_store.py:23-31`) 🟢
5. `_collection = client.get_or_create_collection("mediclaw_kb")`; seta `_collection` e retorna. (`vector_store.py:32-34`) 🟢

## Fluxos Alternativos

- **[`CHROMA_PERSIST_DIR` ausente]:** `KeyError` cru (sem fallback) — lacuna de configuração. 🟢
- **[Concorrência]:** o double-checked locking garante única criação; o segundo thread re-verifica e retorna a instância existente. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| ChromaDB `PersistentClient` | Vector store persistente | criado no path de `CHROMA_PERSIST_DIR` |
| ChromaDB `Settings` | Config do cliente | `anonymized_telemetry=False`, `product_telemetry=NoopProductTelemetry` |
| `apps.rag.services.telemetry_noop` | Telemetria no-op | `NoopProductTelemetry` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Singleton thread-safe com double-checked locking | `vector_store.py:7-34` | 🟢 |
| Telemetria ChromaDB desativada (evita incompatibilidade posthog 7.x) | `telemetry_noop.py:1-14`; `vector_store.py:23-31` | 🟢 |
| `os.environ` direto fora de `settings.py` | `vector_store.py:21-23` | 🟢 |
| `ANONYMIZED_TELEMETRY` via `setdefault` | `vector_store.py:23` | 🟢 |

## Riscos e Lacunas

- 🔴 `CHROMA_PERSIST_DIR` ausente → `KeyError` cru, sem mensagem amigável.
- 🔴 Convenção de env violada (`os.environ` direto em `vector_store.py:21`).
- 🟡 `setdefault` não sobrescreve `True` pré-existente no ambiente — se o env definiu `ANONYMIZED_TELEMETRY=True`, a telemetria fica ligada apesar da intenção do código.

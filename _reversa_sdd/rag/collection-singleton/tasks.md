# RAG / Collection Singleton, Tarefas de Implementação

> Sequência executável para reimplementar o singleton do vector store a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Deps ChromaDB
- [ ] Env `CHROMA_PERSIST_DIR`

## Tarefas

- [ ] **T-01**, `NoopProductTelemetry` com `capture` no-op
  - Origem no legado: `apps/rag/services/telemetry_noop.py:8-14`
  - Confiança: 🟢

- [ ] **T-02**, `get_collection` singleton com double-checked locking
  - Origem no legado: `apps/rag/services/vector_store.py:14-34`
  - Critério de pronto: `_collection` setada → retorna; senão inicializa sob lock com re-check; `makedirs`; `get_or_create_collection("mediclaw_kb")`
  - Confiança: 🟢

- [ ] **T-03**, PersistentClient com telemetria desativada
  - Origem no legado: `apps/rag/services/vector_store.py:23-31`
  - Critério de pronto: `anonymized_telemetry=False` + `NoopProductTelemetry`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Duas chamadas → mesma instância de coleção
- [ ] **TT-02**, Concorrência (threads) → coleção única
- [ ] **TT-03**, `CHROMA_PERSIST_DIR` ausente → `KeyError`
- [ ] **TT-04**, PersistentClient com telemetria no-op (mock ChromaDB)

## Ordem Sugerida

1. T-01 → T-02 → T-03.
2. Testes TT-01 a TT-04 (mockar ChromaDB).

## Lacunas Pendentes (🔴)

- [ ] Ler `CHROMA_PERSIST_DIR` via `settings.py` e dar fallback amigável.
- [ ] Garantir `ANONYMIZED_TELEMETRY` forçado a `False` (hoje `setdefault` não sobrescreve env `True`).

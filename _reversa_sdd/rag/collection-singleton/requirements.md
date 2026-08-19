# RAG / Collection Singleton — Requisitos

> Contrato operacional do caso de uso **Singleton do vector store** (`get_collection`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Garante uma **única** coleção ChromaDB `mediclaw_kb` por processo, com inicialização lazy e thread-safe (double-checked locking). Desativa a telemetria do ChromaDB (incompatibilidade posthog 7.x).

## Regras de Negócio

- **RN-01** — `get_collection()` retorna a instância `_collection` já setada; senão inicializa sob lock. 🟢
- **RN-02** — Double-checked locking: re-verifica `_collection` após adquirir `_lock`. 🟢
- **RN-03** — `CHROMA_PERSIST_DIR` obrigatório do env (`os.environ[...]`); ausente → `KeyError`. 🟢
- **RN-04** — `makedirs(CHROMA_PERSIST_DIR, exist_ok=True)`. 🟢
- **RN-05** — Telemetria desativada via `NoopProductTelemetry` e `ANONYMIZED_TELEMETRY=False` (`setdefault`). 🟢
- **RN-06** — Coleção criada/obtida com `get_or_create_collection("mediclaw_kb")`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Retornar singleton | Must | Duas chamadas → mesma instância de coleção |
| RF-02 | Inicializar lazy | Must | `_collection` só criada na primeira chamada |
| RF-03 | Ser thread-safe | Must | Concorrência não cria coleções duplicadas |
| RF-04 | Desativar telemetria | Must | `PersistentClient` usa `NoopProductTelemetry` |

## Critérios de Aceitação

```gherkin
Dado o processo com CHROMA_PERSIST_DIR definido
Quando chamo get_collection duas vezes
Então ambas retornam a mesma instância da coleção mediclaw_kb

Dado CHROMA_PERSIST_DIR ausente do env
Quando chamo get_collection
Então levanta KeyError

Dado um PersistentClient criado por get_collection
Quando inicio
Então a telemetria usa NoopProductTelemetry e ANONYMIZED_TELEMETRY=False
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/rag/services/vector_store.py:14-34` | `get_collection` | 🟢 |
| `apps/rag/services/vector_store.py:7-9` | `_client`, `_collection` (module-scope) | 🟢 |
| `apps/rag/services/telemetry_noop.py:8-14` | `NoopProductTelemetry.capture` | 🟢 |
| `config/settings.py` / env | `CHROMA_PERSIST_DIR`, `ANONYMIZED_TELEMETRY` | 🟢 |

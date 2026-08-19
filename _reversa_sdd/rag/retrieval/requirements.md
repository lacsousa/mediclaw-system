# RAG / Retrieval — Requisitos

> Contrato operacional do caso de uso **Busca por similaridade** (`search`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Recupera os chunks mais relevantes da base de conhecimento para o contexto da resposta. Não é endpoint: função de serviço consumida pelo `ai_engine` (`_build_messages`), que chama `search(query, k=RAG_TOP_K=5, min_score=RAG_MIN_SCORE=0.75)`. Converte distância L² em score e filtra por limiar.

## Regras de Negócio

- **RN-01** — Coleção vazia (`count() == 0`) → retorna `[]`. 🟢
- **RN-02** — Query embedded via singleton `_emb` (`OpenAIEmbeddings`). 🟢
- **RN-03** — `n_results = min(k, coll.count())`. 🟢
- **RN-04** — Score = `max(0.0, 1.0 - (dist / 2.0))` (distância L²). 🟡 — a fórmula só equivale a similaridade cosseno sob a hipótese de **vetores normalizados**; a coleção não fixa métrica/normalização no metadata, então a semântica do threshold é dependente de configuração [Revisão Codex]
- **RN-05** — Chunk com `score < min_score` é descartado. 🟢
- **RN-06** — Resultado **presumivelmente** ordenado por score descrescente. 🟡 — a unit não executa `sort`; a ordem depende do comportamento transitivo do ChromaDB após conversão/filtro [Revisão Codex]
- **RN-07** — Resultado = `{content, source=title, chunk_id=chunk_index, document_id, score=round(score, 4)}`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Buscar por similaridade | Must | `search(query, k, min_score)` → lista de chunks ordenada por score |
| RF-02 | Tratar coleção vazia | Must | `count() == 0` → `[]` |
| RF-03 | Aplicar limiar | Must | Chunks com score < `min_score` descartados |
| RF-04 | Limitar resultados | Must | No máximo `k` chunks (limitado ao `count()`) |
| RF-05 | Formatar resultado | Must | Chunk com `content`, `source`, `chunk_id`, `document_id`, `score` |

## Critérios de Aceitação

```gherkin
Dado uma base com documentos indexados
Quando chamo search(query, k=5, min_score=0.75)
Então retorna até 5 chunks com score >= 0.75, ordenados por score desc

Dado uma base vazia
Quando chamo search(query)
Então retorna []

Dado uma base onde nenhum chunk atinge o limiar
Quando chamo search(query, min_score=0.9)
Então retorna []
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/rag/services/retriever.py:19-52` | `search` | 🟢 |
| `apps/rag/services/retriever.py:7-16` | `_get_embeddings` (singleton `_emb`) | 🟢 |
| `apps/ai_engine/orchestrator.py:124-128` | chamada `search(query, k=RAG_TOP_K, min_score=RAG_MIN_SCORE)` | 🟢 |
| `config/settings.py` | `RAG_TOP_K` (5), `RAG_MIN_SCORE` (0.75) | 🟢 |

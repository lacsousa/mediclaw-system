# RAG / Retrieval, Tarefas de Implementação

> Sequência executável para reimplementar o retrieval a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] `get_collection` singleton (ver collection-singleton)
- [ ] `OpenAIEmbeddings` configurado (`EMBEDDING_MODEL`)

## Tarefas

- [ ] **T-01**, `_get_embeddings` como singleton module-scope
  - Origem no legado: `apps/rag/services/retriever.py:7-16`
  - Critério de pronto: instância única reutilizada entre chamadas
  - Confiança: 🟢

- [ ] **T-02**, `search` com early-return para coleção vazia e `n_results=min(k, count)`
  - Origem no legado: `apps/rag/services/retriever.py:25-34`
  - Confiança: 🟢

- [ ] **T-03**, Conversão distância → score e filtro por `min_score`
  - Origem no legado: `apps/rag/services/retriever.py:40-42`
  - Critério de pronto: `max(0.0, 1.0 - dist/2.0)`; descarta `< min_score`
  - Confiança: 🟢

- [ ] **T-04**, Formatação e ordenação do resultado
  - Origem no legado: `apps/rag/services/retriever.py:43-51`
  - Critério de pronto: `{content, source, chunk_id, document_id, score}` ordenado por score desc
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Base com documentos → até k chunks ordenados com score ≥ limiar
- [ ] **TT-02**, Base vazia → `[]`
- [ ] **TT-03**, Nenhum chunk atinge o limiar → `[]`
- [ ] **TT-04**, `n_results` limitado ao `count()` quando k maior que a base
- [ ] **TT-05**, Integração: orquestrador chama com `RAG_TOP_K=5`, `RAG_MIN_SCORE=0.75`

## Ordem Sugerida

1. T-01 → T-02 → T-03 → T-04.
2. Testes TT-01 a TT-05 (mockar ChromaDB e embeddings).

## Lacunas Pendentes (🔴)

- [ ] Alinhar default de `min_score` da assinatura (0.40) com o env/contrato (0.75).

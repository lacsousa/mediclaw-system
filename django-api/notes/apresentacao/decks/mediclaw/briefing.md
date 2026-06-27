# Briefing: mediclaw
**Fonte:** decks/mediclaw/references/ (README.md, roteiro-apresentacao.md, tarefas-trabalho-final.md, evolucao-projeto.md)
**Data da extração:** 2026-06-26

---

## Essência em uma frase

MediClaw é uma plataforma web de apoio clínico que permite ao médico interagir com um assistente de IA durante o atendimento, obtendo hipóteses diferenciais e evidências indexadas via RAG, com guardrails éticos que garantem que a IA jamais emite diagnóstico ou prescrição.

---

## Contexto acadêmico

- **Disciplina:** Construção de APIs para Inteligência Artificial (pós-graduação UFG)
- **Equipe:** Adriano Soares, Júlio César Pires, Luciano Sousa, Mara Pereira, Pedro Diehl
- **Prazo:** 30/06/2026 (4 dias)
- **Formato entregável:** vídeo de até 10 minutos + repositório público GitHub
- **Avaliação do professor (simulada):** projeto vai além do mínimo em todas as dimensões técnicas; dois pontos críticos pendentes — repositório público e vídeo

---

## Conceitos-chave (candidatos a slide)

1. **O problema** — Lacuna entre coleta de dados de saúde e ação clínica; complexidade de interpretação, generalismo de recomendações, acesso limitado a expertise. Sugestão visual: `d3-comparacao` (3 dimensões do problema lado a lado)

2. **O que é o MediClaw** — CDSS conversacional: médico descreve o paciente em linguagem natural, IA devolve hipóteses com embasamento em evidências, dados são capturados automaticamente da conversa. Sugestão visual: `d3-fluxo` (médico → chat → IA → resposta + dados persistidos)

3. **Evolução de escopo (pivot)** — De plataforma de longevidade para o usuário final → para CDSS orientado ao médico. Tabela proposta x entregue. Sugestão visual: `d3-comparacao` (duas colunas: proposta original vs. implementação)

4. **Arquitetura full-stack** — Next.js 16 + Django 5.2 + PostgreSQL 16 + ChromaDB; 3 camadas: Apresentação, Serviços, Inteligência. Sugestão visual: `d3-fluxo` (diagrama de componentes das 4 camadas com setas)

5. **Pipeline de IA (7 etapas)** — Guardrail pré → Captura conversacional → RAG → Montagem do prompt → LLM (stream/síncrono) → Guardrail pós → Disclaimer. Sugestão visual: `d3-fluxo` (pipeline sequencial vertical com 7 nós)

6. **Guardrails determinísticos** — Bloqueio de urgência, diagnóstico, prescrição e gibberish antes e depois do LLM. TP=100%, FP=0% em 33 prompts de avaliação. Custo zero (sem chamada de API). Sugestão visual: `d3-fluxo` (bifurcação: bloqueado → resposta canned | liberado → segue pipeline)

7. **RAG: base de conhecimento** — Upload PDF/TXT/MD → chunking (1000 chars, overlap 200) → embeddings `text-embedding-3-small` → ChromaDB → recuperação por similaridade coseno (score ≥ 0.75). Sugestão visual: `d3-fluxo` (pipeline de ingestão + recuperação)

8. **Provider pattern** — Troca OpenAI ↔ Gemini via variável de ambiente, sem mudança de código. Abstração via `Protocol` Python. Sugestão visual: `d3-comparacao` (dois providers lado a lado)

9. **Qualidade e testes** — 137 testes backend (pytest + PostgreSQL real) + ~40 frontend (Vitest). Cobertura: guardrails, orquestrador, skills, RAG, autenticação. Sugestão visual: `card_metricas`

10. **Segurança e ética** — JWT (30 min access / 1 dia refresh), multi-tenancy por médico, rate limiting (10 msg/min no chat), CORS restrito, disclaimer obrigatório em toda resposta clínica, aceite de termos LGPD obrigatório no cadastro. Sugestão visual: `d3-fluxo` ou lista de camadas de controle

11. **Limitações reconhecidas** — Guardrails por regex (bypassáveis), audit trail stub, JWT em localStorage e query string SSE, ChromaDB single-node. Sugestão visual: `card_lista` ou tabela simples

12. **Resultados e próximos passos** — Comparativo mínimo exigido vs. MediClaw. Trabalhos futuros: pgvector, cookies httpOnly, guardrails ML, Celery. Sugestão visual: `d3-comparacao` ou `card_metricas`

---

## Dados e números

| Métrica | Valor |
|---|---|
| Testes backend | 137 (pytest + PostgreSQL 16 real) |
| Testes frontend | ~40 (Vitest + Testing Library) |
| Endpoints com IA | 4 (mínimo exigido: 2) |
| Guardrails: taxa de acerto | TP=100%, FP=0% em 33 prompts |
| JWT access token | 30 minutos |
| JWT refresh token | 1 dia |
| Rate limit chat | 10 mensagens/min |
| Rate limit usuário | 60 req/min |
| Upload máximo KB | 10 MB |
| Chunking RAG | 1000 chars, overlap 200 |
| Score mínimo RAG | 0.75 (similaridade coseno) |
| Stack backend | Django 5.2, DRF 3.16, Python 3.12, PostgreSQL 16, LangChain 0.3, ChromaDB 0.5 |
| Stack frontend | Next.js 16, React 19, TypeScript, Chakra UI v3 |
| Épicos concluídos | E1–E6 (E7 Hardening pendente) |
| Prazo entrega | 30/06/2026 |

---

## Trechos de código emblemáticos

### Pipeline do orquestrador (pseudo-código)
```python
# apps/ai_engine/orchestrator.py
def generate(user_id, conversation_id, query):
    if blocked := guardrails.check_input(query):
        return canned_response(blocked)
    data = capture_patient_data(query)
    context = rag.search(query)
    summary = health_summary(user_id)
    prompt = build_system_prompt(context, summary)
    response = llm.complete(prompt, query)
    if blocked := guardrails.check_output(response):
        return canned_response(blocked)
    return append_disclaimer(response)
```

### Padrão de envelope de resposta
```json
{
  "data": { "content": "...", "tokens_used": 312, "blocked_by_guardrail": false },
  "error": null,
  "meta": {}
}
```

### Evento SSE de streaming
```json
{"type": "token", "content": "Con"}
{"type": "citation", "source": "Diretrizes AHA 2023"}
{"type": "done", "tokens_used": 312, "patient_id": 7}
```

---

## Narrativa sugerida

**Arco da apresentação (~10 min):**

1. **Problema** (~1 min) — O médico afoga em dados fragmentados; não há tempo para consultar evidências durante a consulta.
2. **Solução: o que é o MediClaw** (~1 min) — CDSS conversacional. Médico fala com a IA como falaria com um colega; a IA responde com embasamento e registra os dados automaticamente.
3. **Pivot de escopo** (~30 seg) — Começou como app de longevidade, evoluiu para CDSS orientado ao médico. Por quê? Coerência ético-legal e melhor modelo de dados.
4. **Arquitetura** (~2 min) — 3 camadas + diagrama de componentes + stack técnica.
5. **Pipeline de IA** (~2 min) — As 7 etapas do orquestrador, com destaque para guardrails e RAG.
6. **Qualidade e segurança** (~1 min) — 137 testes, envelope API, JWT, multi-tenancy, LGPD.
7. **Demo (referência)** (~30 seg) — Mencionar que o vídeo mostra: login, chat streaming, guardrail bloqueando, upload KB, Swagger.
8. **Limitações e próximos passos** (~30 seg) — Honestidade: audit stub, JWT em query string SSE, migração para pgvector.
9. **Resultados vs. mínimo exigido** (~30 seg) — Tabela comparativa; CTA final.
10. **Equipe** (~30 seg) — 5 membros.

---

## Screenshots disponíveis

Pasta: `references/screenshots/` — 4 capturas da aplicação em execução local:

| Arquivo | Tela | O que mostra |
|---|---|---|
| `Captura de Tela 2026-06-26 às 14.46.10.png` | Landing page | Headline "Orientação em saúde com inteligência artificial", 3 cards de features (Crie sua conta / Converse com a IA / Histórico salvo), CTAs verde ciano, rodapé com disclaimer |
| `Captura de Tela 2026-06-26 às 14.46.35.png` | Login | Formulário clean com e-mail e senha, botão "Entrar" verde ciano |
| `Captura de Tela 2026-06-26 às 14.46.53.png` | Lista de conversas | Sidebar verde escuro (MediClaw / Assistente de saúde) com navegação Chat IA / Pacientes / Conhecimento; lista de 5 conversas por nome de paciente (Paulo, João, Pedro, Maria, João Silva) |
| `Captura de Tela 2026-06-26 às 14.47.12.png` | Chat com IA | Resposta formatada em markdown para o paciente "Paulo" sobre atividades físicas; sidebar idêntica ao anterior |

Identidade visual do frontend: fundo off-white, verde ciano (`#0D9488` aprox.) como cor primária nos botões e sidebar.

## Lacunas

- Sem capturas de: tela de pacientes, base de conhecimento, admin de métricas, guardrail bloqueando na prática. Para esses, usar descrição textual ou ícones.
- Sem métricas de latência (tempo médio de resposta do pipeline) — não encontrado no material.
- Sem informação sobre uso em produção ou usuários reais — projeto é acadêmico/MVP.
- ADRs detalhados estão em `specs/ARCHITECTURE.md` do repositório do projeto; o roteiro de apresentação resume os 8 ADRs principais.

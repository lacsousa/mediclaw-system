# Roteiro de Apresentação — MediClaw
**Disciplina:** Construção de APIs para Inteligência Artificial  
**Projeto:** MediClaw — Assistente Inteligente de Apoio à Longevidade e Bem-Estar  
**Prazo de entrega:** 30/06/2026

---

## Estrutura Geral (sugestão de tempo para vídeo de 10 min)

| Bloco | Seção | Tempo sugerido |
|---|---|---|
| 1 | Introdução | ~2 min |
| 2 | Arquitetura | ~2 min |
| 3 | Documentação e Qualidade | ~1 min |
| 4 | Pipeline de IA | ~2 min |
| 5 | Segurança e Ética Médica | ~1 min |
| 6 | Demonstração | ~1 min |
| 7 | Conclusão | ~30 seg |
| 8 | Apresentação da Equipe | ~30 seg |

---

## 1. INTRODUÇÃO

### Problema
Profissionais de saúde e pacientes têm dificuldade em consolidar dados biométricos dispersos (peso, sono, atividade, nutrição) e obter orientações preventivas embasadas em evidências científicas de forma rápida e acessível durante o atendimento.

### O que é o MediClaw
O **MediClaw** é uma plataforma web full-stack de apoio à decisão clínica (CDSS — Clinical Decision Support System) que combina:

- **Django REST Framework** como backend API
- **LLMs configuráveis** (OpenAI GPT-4o-mini ou Google Gemini) para geração de linguagem
- **RAG com ChromaDB** para respostas embasadas em literatura científica
- **Next.js** como frontend interativo

O sistema permite que médicos interajam com um assistente de IA durante atendimentos, consultando dados biométricos dos pacientes e recebendo orientações preventivas em tempo real via streaming.

### Restrição Crítica (Ética Médica)
> **A IA nunca emite diagnóstico médico ou prescrição.** Toda resposta é de caráter educativo, preventivo e obrigatoriamente acompanhada de disclaimer médico — restrição implementada por guardrails determinísticos na entrada e na saída do LLM.

### Contexto Acadêmico
Projeto desenvolvido para a disciplina **Construção de APIs para Inteligência Artificial**, implementando todos os requisitos exigidos e indo além do mínimo em múltiplas dimensões.

---

## 2. ARQUITETURA

### Visão Geral (Monorepo Full-Stack)

```
react-painel/          ← Frontend Next.js + TypeScript
django-api/            ← Backend Django 5.2 + DRF
```

### Diagrama de Componentes

```
React Client (Next.js)
        │ HTTPS / SSE
        ▼
Django/DRF (uvicorn ASGI)
        │
   ┌────┴──────────────────────┐
   │            │              │
   ▼            ▼              ▼
PostgreSQL   ai_engine        rag
(ORM)     (orchestrator,  (ingestion,
           guardrails,     retriever)
           skills)              │
              │                 ▼
              ▼             ChromaDB
        LLM Provider       (vector store)
      (OpenAI / Gemini)
```

### Stack Técnica

**Backend:**
- Python 3.12 + Django 5.2 + DRF 3.16
- PostgreSQL 16 com `psycopg[binary]` 3.x
- LangChain 0.3 para orquestração de RAG
- ChromaDB 0.5 como vector store local (MVP)
- uvicorn ASGI para suporte a streaming SSE
- structlog para logs estruturados em JSON

**Frontend:**
- Next.js (webpack) + TypeScript
- Comunicação via REST e EventSource (SSE)

**Infra:**
- Docker + Docker Compose + DevContainer
- GitLab CI com stages de lint (Black) e test (pytest + PostgreSQL 16 real)

### Módulos do Backend (Monolito Modular)

| App Django | Responsabilidade |
|---|---|
| `accounts` | Usuários, autenticação JWT, registro |
| `patients` | Gestão de pacientes por médico (multi-tenancy) |
| `health_logs` | Logs biométricos: peso, sono, atividade, nutrição |
| `conversations` | Histórico de chat, mensagens, streaming SSE |
| `ai_engine` | Orquestrador, prompts, guardrails, skills, providers |
| `rag` | Ingestão de documentos, vector store, retrieval |
| `audit` | ActivityLog, métricas internas |
| `common` | Exceções, renderers, middlewares, permissões |

### Decisões Arquiteturais (ADRs)

- **ADR-01:** Django + DRF — maturidade, admin embutido para KB, ecossistema Python alinhado com IA
- **ADR-02:** PostgreSQL 16 — JSONB para metadados, caminho direto para `pgvector` na fase 2
- **ADR-03:** ChromaDB local — zero infra externa no MVP, abstração LangChain facilita migração futura
- **ADR-04:** JWT stateless — sem Redis no MVP, access 30min + refresh 1 dia
- **ADR-05:** SSE (Server-Sent Events) — nativo no browser, unidirecional suficiente para chat
- **ADR-06:** Provider-agnóstico de LLM — sem lock-in, troca via variável de ambiente
- **ADR-07:** LangChain — splitters, loaders, retrievers prontos para RAG
- **ADR-08:** Guardrails determinísticos — latência zero, auditáveis, sem custo de chamada LLM

### Padrão de Resposta da API
Todos os endpoints retornam envelope uniforme via `EnvelopeJSONRenderer`:

```json
// Sucesso
{ "data": { ... }, "error": null, "meta": { "total": 10, "page": 1 } }

// Erro
{ "data": null, "error": { "code": "GUARDRAIL_BLOCKED", "message": "..." } }
```

---

## 3. DOCUMENTAÇÃO E QUALIDADE DE CÓDIGO

### Padrão BMAD
Toda a documentação do projeto foi gerada seguindo o padrão **BMAD (Business, Model, Architecture, Data)**, organizada na pasta `specs/`:

- **PRD.md** — Requisitos de produto e regras de negócio
- **ARCHITECTURE.md** — Decisões arquiteturais (ADRs), stack detalhada, fluxo de dados, schema de banco
- **PROJECT-CONTEXT.md** — Contexto completo para agentes de IA e desenvolvedores (lido antes de qualquer implementação)
- **TASKS.md** — Épicos e tarefas de implementação sequenciais

Esse padrão garante que tanto desenvolvedores humanos quanto agentes de IA tenham o contexto necessário para trabalhar no projeto com coerência.

### Alternância de Modelos — Padrão Provider

O sistema implementa um **padrão provider** que permite alternar entre modelos de linguagem sem nenhuma mudança de código, apenas via variável de ambiente:

```bash
LLM_PROVIDER="openai"     # Usa GPT-4o-mini + text-embedding-3-small
LLM_PROVIDER="gemini"     # Usa Gemini Flash
```

A abstração é definida em `apps/ai_engine/providers/base.py` como um `Protocol` Python, com implementações independentes:

- `OpenAIProvider` — stream, complete, complete_json via SDK OpenAI ≥1.30
- `GeminiProvider` — stream, complete, complete_json via SDK Google Generative AI

Isso evita lock-in de fornecedor e permite comparar custo e qualidade entre provedores sem refatoração.

### Suite de Testes

| Camada | Framework | Quantidade |
|---|---|---|
| **Backend** | pytest + pytest-django | **137 testes** |
| — Guardrails (urgência, diagnóstico, prescrição, gibberish, output LLM) | — | 22 testes |
| — Orquestrador, skills, RAG, autenticação | — | 115 testes |
| **Frontend** | Vitest + Testing Library | **~40 testes** |
| **Total geral** | — | **~177 testes** |

Os testes de backend rodam contra PostgreSQL 16 real (não SQLite), garantindo fidelidade ao ambiente de produção. O CI do GitLab executa a suite completa em cada push.

### Outras Ferramentas de Qualidade

- **Black + pre-commit** — formatação automática em cada commit
- **Swagger UI** (`GET /swagger/`) e **ReDoc** (`GET /redoc/`) integrados via drf-yasg
- **Healthcheck** (`GET /health/`) — verifica Postgres e ChromaDB em tempo real
- **Conventional Commits** — histórico de git semântico

---

## 4. PIPELINE DE IA

O coração do sistema é o orquestrador em `apps/ai_engine/orchestrator.py`, que implementa um pipeline sequencial com 7 etapas distintas.

### Fluxo Completo do Pipeline

```
Usuário digita pergunta
        │
        ▼
[1] GUARDRAIL DE ENTRADA
        │ Bloqueado? → Retorna mensagem educativa (sem chamar LLM)
        │ Liberado?  ↓
        ▼
[2] CAPTURA DE DADOS (Skills)
        │
        ▼
[3] BUSCA RAG (Retrieval)
        │
        ▼
[4] MONTAGEM DO PROMPT
        │
        ▼
[5] CHAMADA AO LLM (streaming ou síncrono)
        │
        ▼
[6] GUARDRAIL DE SAÍDA
        │
        ▼
[7] PERSISTÊNCIA + DISCLAIMER
        │
        ▼
   Resposta ao usuário
```

### Detalhamento de Cada Etapa

**[1] Guardrail de Entrada (`guardrails.check_input`)**
Filtros determinísticos por keywords e regex aplicados ao prompt do usuário *antes* de qualquer chamada ao LLM. Detecta e bloqueia:
- Pedidos de **diagnóstico médico** ("você tem", "é provavelmente", "o diagnóstico é")
- Pedidos de **prescrição** ("tome", "prescrevia", "dosagem de")
- Situações de **urgência/emergência** ("dor no peito", "não consigo respirar")
- **Gibberish / texto sem sentido** (proteção contra prompt injection)

Custo zero: sem chamada de API, sem latência adicional, 100% auditável.

**[2] Captura de Dados — Skills**
O orquestrador chama automaticamente as skills relevantes para enriquecer o contexto:
- `health_summary(user_id)` — agrega dados biométricos dos últimos 7 dias (média de peso, horas de sono, atividade física, notas de nutrição)
- `calculate_bmi(weight, height)` — cálculo de IMC
- `convert_units(value, from, to)` — conversão de unidades de saúde

**[3] Busca RAG — Retrieval Augmented Generation**
Busca semântica na base de conhecimento indexada (ChromaDB):
- Embedding da query com `text-embedding-3-small` (OpenAI, 1536 dimensões)
- Recupera os **top-5 chunks** com score de similaridade ≥ 0.75
- Chunks são trechos de documentos científicos/diretrizes indexados pelo admin
- Garante que as respostas são embasadas em fontes confiáveis

**[4] Montagem do Prompt**
Constrói o contexto completo para o LLM:
```
SYSTEM_PROMPT
  ├── Contexto RAG: trechos dos documentos relevantes
  ├── Dados de saúde do paciente: resumo 7 dias
  └── Instrução de disclaimer obrigatório

HISTORY: últimas 6 mensagens da conversa
USER: pergunta atual
```

**[5] Chamada ao LLM — Dois Modos**

*Modo Síncrono* (`POST /api/v1/conversations/{id}/messages/`):
- Aguarda resposta completa antes de retornar
- Retorna a mensagem serializada com `tokens_used` e `metadata` (citações)

*Modo Streaming SSE* (`GET /api/v1/conversations/{id}/stream/`):
- Response via `StreamingHttpResponse` com ASGI (uvicorn)
- Tokens entregues ao frontend token a token via `EventSource`
- Eventos tipados: `{"type":"token","content":"..."}`, `{"type":"citation","source":"..."}`, `{"type":"done","tokens_used":N}`

**[6] Guardrail de Saída (`guardrails.check_output`)**
Verifica a resposta gerada pelo LLM antes de entregá-la ao usuário:
- Se a resposta do LLM mesmo assim contiver diagnóstico ou prescrição, ela é **interceptada e substituída** por mensagem educativa padrão
- Caso contrário, injeta automaticamente o **disclaimer médico** ao final

**[7] Persistência e Disclaimer**
- Persiste `Message(role=ASSISTANT)` com `tokens_used`, `blocked_by_guardrail`, `metadata` (citações, latência, modelo)
- Registra evento no audit log: `MESSAGE_SENT` com metadados de uso (sem PII)
- Disclaimer médico obrigatório injetado em toda resposta com viés clínico

### Endpoints de IA Implementados (4 no total — mínimo exigido: 2)

| Endpoint | Tipo | Pipeline |
|---|---|---|
| `POST /api/v1/conversations/{id}/messages/` | Síncrono | Guardrail + Captura + RAG + LLM + Guardrail saída |
| `GET /api/v1/conversations/{id}/stream/` | Streaming SSE | Mesmo pipeline, token a token |
| `POST /api/v1/admin/knowledge/upload/` | Ingestão | Embeddings + indexação ChromaDB |
| `GET /api/v1/health/summary/` | Skill | Agregação biométrica + análise por IA |

---

## 5. SEGURANÇA E ÉTICA MÉDICA

### Autenticação — Tokens JWT

O sistema usa **JSON Web Tokens (JWT)** via `djangorestframework-simplejwt`:

- **Access Token:** validade de **30 minutos** — curta o suficiente para limitar exposição
- **Refresh Token:** validade de **1 dia** — permite renovar o access sem novo login
- **Header padrão:** `Authorization: Bearer <token>`
- **Stateless:** sem Redis ou sessões em servidor no MVP
- **Fluxo:** login → recebe par (access + refresh) → usa access nas requisições → ao expirar, usa refresh para obter novo access

> **Limitação documentada:** No endpoint de streaming SSE, o token é passado via query string (`?token=...`) por limitação técnica do `EventSource` nativo do browser, que não suporta headers customizados. O risco é mitigado pelo access token de curta duração. Mitigação futura: proxy WebSocket ou cookie httpOnly.

### Rate Limiting

| Perfil | Limite |
|---|---|
| Anônimo | 30 requisições/min |
| Usuário autenticado | 60 requisições/min |
| Endpoint de chat | 10 mensagens/min |

### Outras Camadas de Segurança

- **Multi-tenancy:** médicos acessam apenas seus próprios pacientes (`doctor=request.user` em todos os querysets)
- **CORS restrito:** `CORS_ALLOWED_ORIGINS` com origens explícitas — sem `*`
- **CSRF:** API stateless via JWT (sem cookies de sessão)
- **Upload seguro:** limite de 10MB + whitelist de MIME types (PDF, TXT, MD)
- **Sem SQL injection:** Django ORM parametrizado em todos os acessos ao banco
- **Sem log de PII:** filtro customizado no `LOGGING` descarta conteúdo de mensagens e dados biométricos

### Ética Médica e LGPD

- **Guardrails éticos** bloqueiam diagnóstico, prescrição e situações de urgência simulada (pré e pós LLM)
- **Disclaimer obrigatório** injetado automaticamente em toda resposta clínica
- **Consentimento LGPD** explícito no cadastro (`accepted_terms_at` obrigatório — LGPD Art. 11)
- **Cascade delete:** ao deletar usuário, todas conversas, mensagens e logs de saúde são removidos
- **Retenção limitada:** conversas retidas por 90 dias após última atividade (configurável)
- **Minimização de dados:** não coleta nem registra dado além do necessário

---

## 6. DEMONSTRAÇÃO

*Roteiro sugerido para a gravação (sequência de telas):*

1. **Login** → mostrar JWT sendo retornado (`access` + `refresh`)
2. **Dashboard do médico** → listar pacientes
3. **Logs biométricos** → registrar peso/sono de um paciente
4. **Chat (modo streaming)** → fazer pergunta sobre saúde preventiva e mostrar tokens chegando em tempo real via SSE
5. **Guardrail bloqueando** → tentar pedir diagnóstico e mostrar mensagem educativa sendo retornada (sem chamar LLM)
6. **Swagger UI** → mostrar documentação interativa dos endpoints em `/swagger/`
7. **Upload de documento** → fazer ingestão de PDF na base de conhecimento (admin)
8. **Healthcheck** → `GET /health/` mostrando status de Postgres e ChromaDB

*Demonstrar cenário de dado inválido (para critério de avaliação):*
- Enviar payload sem campo `content` → mostrar `VALIDATION_ERROR` estruturado
- Fazer upload com MIME type incorreto → mostrar `INVALID_FILE_TYPE`

---

## 7. CONCLUSÃO

### O que o projeto entrega além do mínimo

| Critério | Mínimo exigido | MediClaw |
|---|---|---|
| Endpoints com IA | 2 | **4 endpoints distintos** |
| Validação de dados | Básica | **Múltiplas camadas** (serializers, guardrails, MIME, limite de mensagens) |
| Tratamento de erros | Básico | **Envelope padronizado** + erros SSE sem quebrar stream |
| Segurança | JWT | **JWT + rate limiting + CORS + multi-tenancy + guardrails éticos** |
| Testes | — | **~177 testes** (137 backend + ~40 frontend) |
| Documentação | README | **Swagger + ReDoc + PRD + ADRs + BMAD** |

### Limitações Documentadas (Trabalho Futuro)

- Audit trail atual é stub (`pass`) — persistência real planejada para fase 2
- Token SSE via query string — mitigação: cookie httpOnly ou proxy WebSocket
- ChromaDB → `pgvector` no PostgreSQL (zero mudança no contrato do retriever)
- Indexação síncrona → Celery + Redis para documentos grandes

### Resultado Geral

O MediClaw demonstra domínio avançado dos conceitos da disciplina: pipeline de IA completo com guardrails éticos, RAG, streaming SSE, provedores intercambiáveis, suite de testes robusta e documentação de nível profissional seguindo o padrão BMAD.

---

## 8. APRESENTAÇÃO DA EQUIPE

| Membro |
|---|
| Adriano Lopes de Mendonça Soares |
| Júlio César Batista Pires |
| Luciano Antônio Cordeiro de Sousa |
| Mara Joziclea Pereira |
| Pedro Ramos Krauze Diehl |

---

*Roteiro gerado em: 26/06/2026*  
*Próximo passo: usar este roteiro para gerar o deck de apresentação (roteiro-apresentacao → apresentacao.pptx)*

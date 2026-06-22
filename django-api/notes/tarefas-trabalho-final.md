# Avaliação do Trabalho Final — MediClaw
**Disciplina:** Construção de APIs para Inteligência Artificial  
**Avaliador (simulado):** Prof. Rogério  
**Data de avaliação:** 22/06/2026  
**Prazo de entrega:** 30/06/2026

---

## Visão Geral do Projeto

O **MediClaw** é um sistema de apoio à decisão clínica (CDSS) que combina Django REST Framework, LLMs (OpenAI / Gemini) e RAG com ChromaDB, entregue como aplicação full-stack (backend Django + frontend Next.js). O cenário escolhido é relevante e realista: médicos interagem com um assistente de IA durante atendimentos.

---

## 1. Funcionalidade de IA ✅ ATENDE (com ressalvas)

### Endpoints de IA implementados (mínimo exigido: 2)

**1 - endpoints com IA**
[django-api/apps/conversations/views.py:103-117](django-api/apps/conversations/views.py#L103-L117) — `POST /api/v1/conversations/{id}/messages/` — LLM com guardrails + RAG (modo síncrono)

**1 - endpoints com IA**
[django-api/apps/conversations/views.py:120-265](django-api/apps/conversations/views.py#L120-L265) — `GET /api/v1/conversations/{id}/stream/` — LLM com streaming SSE, guardrails pré/pós, RAG, captura conversacional

**1 - endpoints com IA**
[django-api/apps/rag/views.py:23-58](django-api/apps/rag/views.py#L23-L58) — `POST /api/v1/admin/knowledge/upload/` — Ingestão de documentos via embeddings (text-embedding-3-small)

**1 - endpoints com IA**
[django-api/apps/health_logs/views.py:87-96](django-api/apps/health_logs/views.py#L87-L96) — `GET /api/v1/health/summary/` — Skill de agregação de saúde com análise por IA

**Além do mínimo:** o projeto entrega 4 endpoints com IA real, com pipelines distintos (streaming, síncrono, embeddings).

### Orquestrador de IA

**1 - endpoints com IA**
[django-api/apps/ai_engine/orchestrator.py:183-258](django-api/apps/ai_engine/orchestrator.py#L183-L258) — `generate()`: Guardrail pré-LLM → Captura de dados → Busca RAG → LLM → Guardrail pós-LLM → Disclaimer

**1 - endpoints com IA**
[django-api/apps/ai_engine/orchestrator.py:261-349](django-api/apps/ai_engine/orchestrator.py#L261-L349) — `generate_stream()`: variante com streaming token a token via SSE

### Provedores configuráveis

**1 - endpoints com IA**
[django-api/apps/ai_engine/providers/openai_provider.py:1-52](django-api/apps/ai_engine/providers/openai_provider.py#L1-L52) — `OpenAIProvider` (stream, complete, complete_json)

**1 - endpoints com IA**
[django-api/apps/ai_engine/providers/gemini_provider.py:1-83](django-api/apps/ai_engine/providers/gemini_provider.py#L1-L83) — `GeminiProvider` (stream, complete, complete_json)

### ⚠️ Ressalva
O arquivo [django-api/apps/ai_engine/urls.py:1](django-api/apps/ai_engine/urls.py#L1) está vazio (`urlpatterns = []`). As rotas de IA estão nos apps `conversations` e `rag`. Isso não é um problema funcional, mas pode causar estranheza na revisão.

---

## 2. Validação de Dados ✅ ATENDE

Validação implementada em múltiplas camadas:

**2 - validação de dados**
[django-api/apps/accounts/serializers.py:6](django-api/apps/accounts/serializers.py#L6) — `PASSWORD_RX` regex + `RegisterSerializer`: e-mail (unicidade), senha (≥8 chars, letra+número), aceite de termos obrigatório

**2 - validação de dados**
[django-api/apps/rag/views.py:27-34](django-api/apps/rag/views.py#L27-L34) — Upload: MIME whitelist (PDF, TXT, MD) + limite de 10 MB

**2 - validação de dados**
[django-api/apps/conversations/views.py:113-114](django-api/apps/conversations/views.py#L113-L114) — Mensagem de chat: `CreateMessageInput` (content obrigatório)

**2 - validação de dados**
[django-api/apps/conversations/views.py:166-175](django-api/apps/conversations/views.py#L166-L175) — Prompt não pode ser vazio no SSE (retorna `VALIDATION_ERROR`)

**2 - validação de dados**
[django-api/apps/conversations/views.py:177-186](django-api/apps/conversations/views.py#L177-L186) — Limite de mensagens: máximo 50 por conversa (`MAX_MESSAGES`)

**2 - validação de dados**
[django-api/apps/ai_engine/guardrails.py:135-144](django-api/apps/ai_engine/guardrails.py#L135-L144) — Guardrails de entrada: diagnóstico, prescrição, urgência, gibberish

---

## 3. Tratamento de Erros ✅ ATENDE

**3 - tratamento de erros**
[django-api/apps/common/exceptions.py:5-19](django-api/apps/common/exceptions.py#L5-L19) — `AppError(code, message, status_code, details)`: exceção base estruturada

**3 - tratamento de erros**
[django-api/apps/common/exceptions.py:31-44](django-api/apps/common/exceptions.py#L31-L44) — `envelope_exception_handler`: envolve todos os erros em `{data, error, meta}`

**3 - tratamento de erros**
[django-api/apps/common/renderers.py:4-12](django-api/apps/common/renderers.py#L4-L12) — `EnvelopeJSONRenderer`: garante contrato uniforme de resposta em todos os endpoints

**3 - tratamento de erros**
[django-api/apps/common/exceptions.py:25-28](django-api/apps/common/exceptions.py#L25-L28) — `LLMProviderError` com HTTP 502 quando o provider de IA falha

**3 - tratamento de erros**
[django-api/apps/conversations/views.py:255-260](django-api/apps/conversations/views.py#L255-L260) — Erros no SSE capturados dentro do gerador e emitidos como `{"type": "error", ...}` sem quebrar o stream

**3 - tratamento de erros**
[django-api/apps/ai_engine/guardrails.py:135-144](django-api/apps/ai_engine/guardrails.py#L135-L144) — Guardrail bloqueado: resposta canned sem chamar o LLM

---

## 4. Logs ✅ ATENDE (com ressalva menor)

**4 - logs**
[django-api/apps/common/logging_config.py:36-79](django-api/apps/common/logging_config.py#L36-L79) — structlog: JSON em produção, colorido em desenvolvimento; nível controlado por `LOG_LEVEL`

**4 - logs**
[django-api/apps/common/middleware.py:11-44](django-api/apps/common/middleware.py#L11-L44) — `RequestIDMiddleware`: `X-Request-ID` automático em cada request e resposta

**4 - logs**
[django-api/apps/common/middleware.py:24-30](django-api/apps/common/middleware.py#L24-L30) — Latência de cada request nos logs (`latency_ms`) calculada por `perf_counter`

**4 - logs**
[django-api/apps/common/middleware.py:47-54](django-api/apps/common/middleware.py#L47-L54) — `UserContextMiddleware`: `user_id` injetado nos logs após autenticação

**4 - logs**
[django-api/apps/ai_engine/orchestrator.py:192-200](django-api/apps/ai_engine/orchestrator.py#L192-L200) — Log de `guardrail_blocked` com fase (input/output) e razão

**4 - logs**
[django-api/apps/conversations/views.py:247-251](django-api/apps/conversations/views.py#L247-L251) — Log de `stream_error` dentro do gerador SSE

### ⚠️ Ressalva — Audit Trail é stub

**4 - logs**
[django-api/apps/audit/services/log.py:1-3](django-api/apps/audit/services/log.py#L1-L3) — `record()` é um stub com `pass`: os eventos (`LOGIN`, `USER_REGISTERED`, `GUARDRAIL_BLOCKED`, `MESSAGE_SENT`, `KB_UPLOAD`) **não são persistidos em banco de dados**. O README reconhece isso como limitação (E7 pendente).

---

## 5. Segurança ✅ ATENDE

**5 - segurança**
[django-api/config/settings.py:130-138](django-api/config/settings.py#L130-L138) — JWT Bearer: access 30 min, refresh 1 dia (`AUTH_HEADER_TYPES = ("Bearer",)`)

**5 - segurança**
[django-api/apps/patients/views.py:41](django-api/apps/patients/views.py#L41) — Multi-tenancy: `doctor=request.user` em todos os querysets de pacientes

**5 - segurança**
[django-api/apps/common/permissions.py:4-10](django-api/apps/common/permissions.py#L4-L10) — `IsAdminRole`: verifica `user.role == "ADMIN"` para endpoints administrativos

**5 - segurança**
[django-api/config/settings.py:122-127](django-api/config/settings.py#L122-L127) — Rate limiting: Anônimo: 30/min · Usuário: 60/min · Chat: 10/min

**5 - segurança**
[django-api/config/settings.py:144-151](django-api/config/settings.py#L144-L151) — CORS: origens explícitas via `CORS_ALLOWED_ORIGINS` (não `*`)

**5 - segurança**
[django-api/apps/accounts/serializers.py:6](django-api/apps/accounts/serializers.py#L6) — Validação de senha: regex `(?=.*[A-Za-z])(?=.*\d).{8,}` (letra + dígito + mínimo 8 chars)

**5 - segurança**
[django-api/apps/ai_engine/guardrails.py:135-150](django-api/apps/ai_engine/guardrails.py#L135-L150) — Guardrails éticos: bloqueio de diagnóstico, prescrição, urgência simulada (input + output do LLM)

### ⚠️ Ressalvas de segurança (reconhecidas no README)
- Token JWT transmitido via **query string** no SSE (`?token=...`) — limitação do `EventSource` nativo. Expõe o token em logs de proxy.
- JWT armazenado em **localStorage** — risco teórico de XSS.
- Ambas são limitações documentadas com mitigações futuras planejadas.

---

## 6. Versionamento ✅ ATENDE

**6 - versionamento**
[django-api/config/urls.py:31-37](django-api/config/urls.py#L31-L37) — Todas as rotas usam prefixo `/api/v1/...`

**6 - versionamento**
[django-api/.gitlab-ci.yml:1-38](django-api/.gitlab-ci.yml#L1-L38) — CI/CD: stages de `lint` (Black + pre-commit) e `test` (pytest com PostgreSQL 16 real)

**6 - versionamento**
[django-api/.pre-commit-config.yaml](django-api/.pre-commit-config.yaml) — Pre-commit hooks: Black para formatação automática

Repositório git ativo (branch `main`).

---

## 7. Documentação ✅ ATENDE (destaque positivo)

**7 - documentação**
[django-api/config/urls.py:24-28](django-api/config/urls.py#L24-L28) — Swagger interativo: `GET /swagger/` via drf-yasg

**7 - documentação**
[django-api/config/urls.py:29](django-api/config/urls.py#L29) — ReDoc: `GET /redoc/`

**7 - documentação**
[django-api/apps/common/views.py:17-38](django-api/apps/common/views.py#L17-L38) — Healthcheck: `GET /health/` retorna status de DB e vector store

**7 - documentação**
[README.md](README.md) — README acadêmico completo: resumo executivo, arquitetura, stack, funcionalidades, limitações, instalação

**7 - documentação**
[django-api/specs/PRD.md](django-api/specs/PRD.md) · [django-api/specs/ARCHITECTURE.md](django-api/specs/ARCHITECTURE.md) — PRD e decisões arquiteturais (ADRs)

**7 - documentação**
[README.md:instalação](README.md#15-instalação-e-reprodutibilidade) — Instruções de instalação passo a passo para backend e frontend

---

## 8. Qualidade do Código ✅ DESTAQUE POSITIVO

**8 - qualidade do código**
[django-api/tests/](django-api/tests/) — **137 testes automatizados** no backend com pytest + pytest-django

**8 - qualidade do código**
[django-api/tests/ai_engine/test_guardrails.py:1-163](django-api/tests/ai_engine/test_guardrails.py#L1-L163) — 22 testes de guardrails: urgência, diagnóstico, prescrição, gibberish, saída do LLM

**8 - qualidade do código**
[react-painel/src/__tests__/](react-painel/src/__tests__/) — ~40 testes de frontend com Vitest + Testing Library

**8 - qualidade do código**
[django-api/apps/ai_engine/providers/](django-api/apps/ai_engine/providers/) — Provider pattern: OpenAI ↔ Gemini intercambiáveis via variável de ambiente `LLM_PROVIDER`

**8 - qualidade do código**
[django-api/apps/common/renderers.py:4-12](django-api/apps/common/renderers.py#L4-L12) — Envelope API uniforme `{data, error, meta}`

Monolito modular (apps por domínio), service layer (views finas — `*/services/*.py`), formatação com Black + pre-commit.

---

## 9. Reprodutibilidade ✅ ATENDE

**9 - reprodutibilidade**
[README.md:instalação](README.md#15-instalação-e-reprodutibilidade) — Passo a passo completo para backend e frontend

**9 - reprodutibilidade**
[django-api/.env.example](django-api/.env.example) — Todas as variáveis de ambiente documentadas com exemplos

**9 - reprodutibilidade**
[django-api/.gitlab-ci.yml:28-37](django-api/.gitlab-ci.yml#L28-L37) — CI roda `pytest` com PostgreSQL 16 real (não SQLite), garantindo fidelidade ao ambiente de produção

**9 - reprodutibilidade**
[django-api/.devcontainer/](django-api/.devcontainer/) — Suporte a DevContainer / GitHub Codespaces para reprodução sem instalação local

`requirements.txt` com hashes SHA256 para instalação determinística. Migrations Django configuradas (`python manage.py migrate`).

---

## Resumo da Avaliação por Critério

| Critério | Status | Nota indicativa | Observação |
|----------|--------|-----------------|------------|
| **Funcionalidade de IA** (≥2 endpoints) | ✅ Implementado e funcional | Excelente | 4 endpoints IA distintos + streaming SSE |
| **Dados válidos e inválidos funcionam** | ✅ Implementado | Excelente | Guardrails + serializers + testes |
| **Executa em outro computador** | ✅ Implementado | Bom | README completo + .env.example + requirements.txt |
| **Validação de dados** | ✅ Implementado | Excelente | Múltiplas camadas |
| **Tratamento de erros** | ✅ Implementado | Excelente | Envelope padronizado |
| **Logs** | ✅ Implementado (audit stub) | Bom | structlog OK; audit não persiste |
| **Segurança** | ✅ Implementado (JWT querystring) | Bom | JWT+rate limiting+CORS; token SSE em query string |
| **Versionamento** | ✅ Implementado | Excelente | v1 nas URLs + CI |
| **Qualidade e documentação** | ✅ Implementado | Excelente | 137 testes + Swagger + README completo |
| **Repositório público** | ⚠️ Verificar | — | Precisa garantir acesso público no GitHub |
| **Apresentação (vídeo)** | ⏳ Pendente | — | Entregável ainda não concluído |

---

## Pontos Fortes (para destacar na apresentação)

1. **Pipeline de IA completo e diferenciado:** guardrails pré e pós-LLM, RAG com ChromaDB, captura conversacional de dados clínicos, streaming SSE em tempo real.
2. **137 testes automatizados** com cobertura de guardrails, orquestrador, skills, RAG e autenticação.
3. **Documentação acadêmica excepcional** no README — evolução do projeto, arquitetura, decisões técnicas e limitações.
4. **Provedores LLM intercambiáveis** (OpenAI ↔ Gemini via variável de ambiente) sem mudança de código.
5. **Swagger/ReDoc** integrado e acessível.

---

## Pontos a Corrigir ou Completar Antes da Entrega

### Crítico
- [ ] **Garantir repositório público no GitHub** (não apenas GitLab). O professor exige link do GitHub para avaliação.
- [ ] **Gravar vídeo de apresentação** de até 10 minutos (demonstração funcional + características técnicas).

### Importante (impacta nota)
- [ ] **Implementar audit trail funcional** — [django-api/apps/audit/services/log.py](django-api/apps/audit/services/log.py): substituir o `pass` por persistência real (tabela `AuditEvent` ou ao menos log estruturado com nível INFO) para que os eventos `LOGIN`, `GUARDRAIL_BLOCKED`, `MESSAGE_SENT` sejam rastreáveis.
- [ ] **Adicionar ao README** uma seção de testes documentando como executar (`pytest tests/ -v` e `npm test`) — apesar de existir no README técnico, deve estar explícito no README raiz.

### Recomendado
- [ ] **Criar pelo menos 1 cenário de teste de dados inválidos demonstrável** durante a apresentação (ex: payload sem `content`, arquivo com MIME incorreto, prompt bloqueado por guardrail).
- [ ] **Adicionar link do Swagger** no README raiz — facilita avaliação do professor.
- [ ] **Verificar se `NEXT_PUBLIC_API_URL` está documentado** no [react-painel/.example.env.local](react-painel/.example.env.local) para garantir reprodutibilidade do frontend.

---

## Observações Finais (perspectiva do professor)

O projeto demonstra **domínio avançado** dos conceitos da disciplina. Vai além do mínimo exigido em todas as dimensões técnicas: entrega streaming SSE, RAG, múltiplos provedores de LLM, guardrails éticos, suite de testes robusta e documentação de nível profissional.

Os dois pontos que podem comprometer a nota são **operacionais**, não técnicos:
1. O repositório precisa estar acessível no GitHub conforme exigido.
2. O vídeo de apresentação é entregável obrigatório e ainda não foi concluído.

O audit trail stub é a única lacuna técnica relevante para os requisitos do trabalho — os demais itens pendentes (E7: testes E2E, hardening de produção, cookies httpOnly) estão bem documentados como trabalhos futuros e não penalizam a avaliação.

**Prazo restante:** 8 dias (entrega: 30/06/2026).

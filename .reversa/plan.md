# Plano de Exploração — MediClaw

> Criado pelo Reversa em 2026-08-19
> Marque cada tarefa com ✅ quando concluída.
> Você pode editar este plano antes de iniciar: adicione, remova ou reordene tarefas conforme necessário.

---

## Fase 1: Reconhecimento 🔍

- [x] **Scout** — Mapeamento de estrutura de pastas e tecnologias
- [x] **Scout** — Análise de dependências e gerenciadores de pacotes
- [x] **Scout** — Identificação de entry points, CI/CD e configurações

## Decisão de organização das specs 🗂️

> Entre o Scout e o Arqueólogo, o Reversa pergunta como você quer organizar as specs (por módulo, caso de uso, endpoint, híbrida, por features ou customizada). A escolha fica persistida em `.reversa/config.toml` na seção `[specs]` e não será reperguntada em execuções futuras. Para reapresentar o menu, remova manualmente a seção.

## Fase 2: Escavação 🏗️

> O Reversa preenche esta seção com os módulos reais após o Scout concluir o reconhecimento.

- [x] **Arqueólogo** — Análise do módulo `accounts` (auth JWT, usuários)
- [x] **Arqueólogo** — Análise do módulo `patients` (CRUD de pacientes)
- [x] **Arqueólogo** — Análise do módulo `health_logs` (logs biométricos)
- [x] **Arqueólogo** — Análise do módulo `conversations` (chat + streaming SSE)
- [x] **Arqueólogo** — Análise do módulo `ai_engine` (orquestrador, guardrails, skills)
- [x] **Arqueólogo** — Análise do módulo `rag` (ingestão, vector store, retrieval)
- [x] **Arqueólogo** — Análise do módulo `audit` (ActivityLog, métricas)
- [x] **Arqueólogo** — Análise do módulo `common` (infra: exceptions, renderer, middleware)

## Fase 3: Interpretação 🧠

- [x] **Detetive** — Arqueologia Git e ADRs retroativos
- [x] **Detetive** — Regras de negócio implícitas e máquinas de estado
- [x] **Detetive** — Matriz de permissões (RBAC/ACL)
- [x] **Arquiteto** — Diagramas C4 (Contexto, Containers, Componentes)
- [x] **Arquiteto** — ERD completo e integrações externas
- [x] **Arquiteto** — Spec Impact Matrix

## Fase 4: Geração 📝

- [x] **Redator** — Specs SDD por componente (8 units, 30 casos de uso)
- [x] **Redator** — OpenAPI (se aplicável) → `openapi/mediclaw.yaml`
- [x] **Redator** — User Stories (se aplicável) → 7 fluxos em `user-stories/`
- [x] **Redator** — Code/Spec Matrix → `traceability/code-spec-matrix.md`

## Fase 5: Revisão ✅

- [x] **Revisor** — Revisão cruzada de specs (Codex, 45 apontamentos, 23 incorporados)
- [ ] **Revisor** — Resolução de lacunas com o usuário (20 perguntas em `questions.md`)
- [ ] **Revisor** — Relatório de confiança final (90.3% preliminar; finalizar após respostas)

---

## Agentes Independentes

> Execute estes agentes quando os recursos estiverem disponíveis — podem rodar em qualquer fase.

- [ ] **Visor** — Análise de interface via screenshots
- [ ] **Data Master** — Análise completa do banco de dados
- [ ] **Design System** — Extração de tokens de design
- [ ] **Tracer** — Análise dinâmica (requer sistema acessível)

---

## Próximo passo

Após o Time de Descoberta concluir e o `_reversa_sdd/` estar populado, você pode disparar um dos fluxos seguintes:

- `/reversa-migrate`: orquestrador do **Time de Migração** (Paradigm Advisor → Curator → Strategist → Designer → Screen Translator → Inspector). Gera as specs do sistema novo. Saída em `_reversa_sdd/migration/` e `_reversa_sdd/screens/`.
- `/reversa-reconstructor`: gera plano bottom-up para reimplementar o software a partir das specs do legado (uma tarefa por sessão).

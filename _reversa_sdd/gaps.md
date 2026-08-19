# Lacunas — MediClaw

> Gerado pelo Revisor em 2026-08-19.
> Itens 🔴 que permanecem sem resposta após a revisão (cruzada via Codex + verificação de código).
> Cada lacuna aponta para a pergunta correspondente em [`questions.md`](questions.md).

---

## Críticas

### LGPD e compliance
- **Retenção de 90 dias não implementada** — sem job de expurgo; soft-delete nunca purga; dados de saúde acumulam indefinidamente. → [Pergunta 1](questions.md#pergunta-1--retenção-lgpd-de-90-dias)
- **Auditoria é stub** — `record()` é `pass`; nenhum evento de segurança/uso é persistido (ADR-007 adia para Epic 3). → [Pergunta 2](questions.md#pergunta-2--auditoria-é-stub-no-mvp)

### Segurança
- **KB com acesso cruzado** — `upload`/`list`/`status`/`delete` sem escopo ao `uploaded_by`; qualquer autenticado pode alterar/deletar documentos de terceiros da base global que alimenta o chat. → [Pergunta 10](questions.md#pergunta-10--kb-com-acesso-cruzado-entre-usuários-p-25)
- **Services de paciente sem validação de tenant** — `ensure_or_create_patient`/`resolve_patient_dob` não cruzam conversa↔médico. → [Pergunta 13](questions.md#pergunta-13--services-de-paciente-sem-validação-de-tenant-p-28)
- **Deduplicação não transacional + merge indefinido** — risco de dados duplicados/perdidos no merge. → [Pergunta 14](questions.md#pergunta-14--deduplicação-não-transacional-e-merge-indefinido-p-30p-31)

### Integridade de dados
- **Atomicidade Postgres ↔ ChromaDB ausente** — vetores órfãos ou registros órfãos em falha intermediária de ingestão/exclusão, sem compensação. → [Pergunta 11](questions.md#pergunta-11--atomicidade-postgres-↔-chromadb-p-38)

### Contratos de API
- **`ValidationError` do DRF vira `UNHANDLED`** — contradiz dezenas de contratos `400 VALIDATION_ERROR` nas specs. → [Pergunta 4](questions.md#pergunta-4--erros-de-validação-viram-unhandled)
- **Código de limite canônico indefinido** — `CONVERSATION_FULL` vs `CONVERSATION_LIMIT_REACHED`. → [Pergunta 3](questions.md#pergunta-3--código-canônico-do-limite-de-mensagens)

---

## Moderadas

### Streaming (SSE)
- **DISCLAIMER ausente no caminho normal do stream** — conformidade LGPD depende do LLM. → [Pergunta 6](questions.md#pergunta-6--disclaimer-ausente-no-streaming-p-22)
- **Guardrail de saída pós-hoc** — conteúdo proibido pode chegar ao cliente antes da supressão. → [Pergunta 7](questions.md#pergunta-7--guardrail-de-saída-pós-hoc-no-streaming-p-35)
- **Turno órfão** — USER persistida sem resposta em falha de provider/desconexão; sem estado/retry. → [Pergunta 8](questions.md#pergunta-8--turno-órfão-no-streaming-p-36p-20)
- **Sem throttle no stream** — caminho mais caro sem rate-limit. → [Pergunta 9](questions.md#pergunta-9--sem-throttle-no-streaming-p-19)
- **`patient_created` sempre False** — flag real nunca preenchida; frontend não distingue paciente criado/existente. → [Pergunta 12](questions.md#pergunta-12--patient_created-sempre-false-r43)

### Robustez de entrada
- **Query params inválidos → 500** — `int()` em `patient_id`/`page` lança `ValueError`; paginação manual sem contrato de entrada. → [Pergunta 16](questions.md#pergunta-16--query-params-inválidos--500-p-32p-33)
- **`persist_user_name` com usuário inexistente → 500** — `User.DoesNotExist` sem mapeamento de contrato. → [Pergunta 15](questions.md#pergunta-15--persist_user_name-com-usuário-inexistente--500-p-39)

### Provedores e métricas
- **Provider Anthropic documentado, ausente no código** — contrato real é OpenAI + Gemini. → [Pergunta 5](questions.md#pergunta-5--provider-anthropic-documentado-ausente-no-código)
- **`tokens_used` conta palavras no stream** — métricas de custo imprecisas. → [Pergunta 19](questions.md#pergunta-19--tokens_used-conta-palavras-no-streaming-r39)
- **Catch-alls mascarando erros** — provider/interno/embedding indistinguíveis. → [Pergunta 20](questions.md#pergunta-20--catch-alls-mascarando-erros)

---

## Contratos OpenAPI / user-stories (requerem regeração)

O `openapi/mediclaw.yaml` e algumas user stories ainda divergem do legado em pontos não incorporados nesta revisão:

- **P-01** — construtos incompatíveis com OAS 3.0.3 (o arquivo precisa de validação de schema).
- **P-08** — status/códigos de autenticação divergem entre história, OpenAPI e specs de accounts.
- **P-10** — regras do `first_name` divergem entre cadastro (sem min), PATCH (`allow_blank=True`) e service de captura (`2 ≤ len ≤ 120`).
- **P-11** — payload de criação admin no OpenAPI não corresponde ao `AdminCreateUserSerializer`.
- **P-12** — histórias/OpenAPI expõem criação/PUT de paciente que não existem (só há `GET`; criação vem do chat).
- **P-13** — schema e envelope de pacientes no OpenAPI usam modelo de dados divergente do `Patient`.
- **P-15** — história pede CRUD completo de logs enquanto o domínio define append-only.
- **P-16** — OpenAPI de health logs usa payload genérico inexistente e omite `DELETE` de detalhe.
- **P-23** — cobertura de auditoria de guardrail/mensagem difere entre REST e stream.

---

## Cosméticas / de processo

- **`document_status` expõe `error_message`** ao consumidor — potencial vazamento de detalhes internos. (`rag/design.md`)
- **Convenção de env violada no RAG** (`os.environ` direto em `vector_store.py:21`, `ingestion.py:34`, `retriever.py:14`); `CHROMA_PERSIST_DIR` ausente → `KeyError` cru. → [Pergunta 18](questions.md#pergunta-18--convenção-de-env-violada-no-rag)
- **`MAX_MESSAGES` duplicado** — hardcoded `50` em `views.py:22` vs env `MAX_MESSAGES_PER_CONVERSATION` em `services/chat.py:7`. (`conversations/design.md`)
- **Catch-all de token no stream** — `except (TokenError, Exception)` rotula qualquer erro como `UNAUTHORIZED`. (`conversations/design.md`)
- **`GuardrailBlockedError` e `IsOwner` como código morto** — manter na spec ou remover. → [Pergunta 17](questions.md#pergunta-17--código-morto-guardrailblockederror-e-isowner)
- **Admin seed não valida `PASSWORD_RX`** — `create_superuser` diverge da política de senha dos serializers. (`accounts/design.md`)
- **Sem promoção de role via API** — mudar `USER`→`ADMIN` exige acesso manual ao banco. (`state-machines.md`)
- **Sem reprocessamento de documento `ERROR`** — KB perdida até re-upload manual. (`state-machines.md`)
- **Sem restauração de conversa soft-deletada** — deleção irreversível na UI. (`state-machines.md`)

---

## Observações de confiança (reclassificadas na revisão)

Estas afirmações foram **reclassificadas** de 🟢 para 🟡 durante a revisão por serem inferência não comprovada pelo código — ver histórico no [relatório de confiança](confidence-report.md):

- Conversão L² → score como cosseno (depende de vetores normalizados, não fixado). (P-44)
- Ordenação por score desc no retrieval (depende de ordem transitiva do ChromaDB). (P-45)
- `user_id` em logs JWT (bind ocorre antes da autenticação DRF). (P-40)
- "Captura nunca quebra o turno" (persist de health data captura só `ValidationError`). (P-37)
- `complete_json` no Protocol de provider (não integra o contrato estrutural). (P-42)
- "Backend valida MIME" (checagem sobre header controlado pelo cliente, sem sniffing). (P-43)
- Validações de timestamp futuro e faixas de sono/nutrição atribuídas aos serializers HTTP (valem apenas na via chat). (P-14, P-41)

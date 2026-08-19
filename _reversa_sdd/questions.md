# Perguntas para Validação — MediClaw

> Gerado pelo Revisor em 2026-08-19 após revisão cruzada (Codex, 45 apontamentos).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Modo de resposta: **chat** — responder diretamente no chat; as respostas serão incorporadas e as perguntas marcadas como ✅ Respondida.

---

## Pergunta 1 — Retenção LGPD de 90 dias

**Contexto:** `CONVERSATION_RETENTION_DAYS=90` documentado, mas não existe job de expurgo; soft-delete nunca purga; dados de saúde acumulam indefinidamente (`conversations/models.py`; `state-machines.md:71`; domain.md R28/D1).
**Spec afetada:** [`_reversa_sdd/domain.md`] [`_reversa_sdd/architecture.md`] [`_reversa_sdd/conversations/requirements.md`]
**Pergunta:** A retenção de 90 dias deve ser implementada no MVP (job de expurgo/purga) ou fica documentada como lacuna para pós-MVP?
**Impacto:** Se for pós-MVP, permanece 🔴 e vira Epic futuro. Se for MVP, a spec ganha o contrato do job de retenção (trigger, regra de janela, soft vs hard delete).

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 2 — Auditoria é stub no MVP

**Contexto:** `record()` em `apps/audit/services/log.py` é `pass` — `USER_REGISTERED`, `LOGIN`, `GUARDRAIL_BLOCKED`, `MESSAGE_SENT`, `KB_UPLOAD`, `KB_DELETE`, `ADMIN_CREATED_USER` são descartados (ADR-007 "auditoria adiada").
**Spec afetada:** [`_reversa_sdd/audit/requirements.md`] [`_reversa_sdd/domain.md` R53/R54] [`_reversa_sdd/user-stories/administracao.md` US-ADM-03]
**Pergunta:** Confirmar que a auditoria fica adiada para o Epic 3 (pós-MVP), conforme ADR-007? E o contrato divergente (`user=` vs `user_id=`) deve ser padronizado no Epic 3?
**Impacto:** Mantém 🔴 no MVP; define o contrato canônico de `record()` para a reimplementação.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 3 — Código canônico do limite de mensagens

**Contexto:** O código dispara `CONVERSATION_FULL` (service e SSE); o PROJECT-CONTEXT.md documenta `CONVERSATION_LIMIT_REACHED`. Nenhum dos dois é canônico na doc.
**Spec afetada:** [`_reversa_sdd/conversations/requirements.md` RN-05/RF-07] [`_reversa_sdd/conversations/design.md`] [`_reversa_sdd/domain.md` R24]
**Pergunta:** Qual é o código oficial do limite de mensagens: `CONVERSATION_FULL` (como o código faz) ou `CONVERSATION_LIMIT_REACHED` (como o PROJECT-CONTEXT documenta)?
**Impacto:** Define o contrato de erro que o frontend/OpenAPI devem consumir; alinha ou corrige PROJECT-CONTEXT.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 4 — Erros de validação viram `UNHANDLED`

**Contexto:** `envelope_exception_handler` mapeia payload DRF com chave `code` para `error`; `serializers.ValidationError` (de `is_valid(raise_exception=True)`) produz `{campo: [erros]}` **sem** `code` → vira `{"code": "UNHANDLED", ...}` em vez de `VALIDATION_ERROR`. Contradiz os contratos `400 VALIDATION_ERROR` em health_logs/accounts/conversations (`apps/common/exceptions.py:31-43`).
**Spec afetada:** [`_reversa_sdd/common/requirements.md` RN-02] (impacta health_logs, accounts, conversations)
**Pergunta:** O handler deve normalizar `ValidationError` do DRF para `code=VALIDATION_ERROR` com `details` por campo (corrigindo o código)? Ou o contrato oficial passa a aceitar `UNHANDLED` em validações?
**Impacto:** Correção de código + specs, ou revisão de todos os critérios `VALIDATION_ERROR` (dezenas de claims).

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 5 — Provider Anthropic documentado, ausente no código

**Contexto:** PROJECT-CONTEXT prevê `LLM_PROVIDER` ∈ {openai, anthropic}; o código implementa `openai` e `gemini` (`get_provider` → `RuntimeError` para qualquer outro).
**Spec afetada:** [`_reversa_sdd/ai_engine/providers/requirements.md` RN-01/RN-02] [`_reversa_sdd/domain.md` R37]
**Pergunta:** O contrato oficial é OpenAI + Gemini (corrigir PROJECT-CONTEXT e specs) ou o Anthropic deve ser implementado como provider no Epic 3/4?
**Impacto:** Corrige a spec para refletir o código, ou adiciona a tarefa de implementar o provider Anthropic.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 6 — DISCLAIMER ausente no streaming (P-22)

**Contexto:** No REST o orquestrador anexa o `DISCLAIMER` se ausente; no `generate_stream` o texto é emitido cru, e o `SYSTEM_PROMPT_TEMPLATE` menciona o disclaimer mas não injeta o texto. Conformidade LGPD depende do LLM no stream.
**Spec afetada:** [`_reversa_sdd/conversations/stream-sse/requirements.md` RN-07] [`_reversa_sdd/ai_engine/design.md`] [`_reversa_sdd/domain.md` R34]
**Pergunta:** No streaming, o `DISCLAIMER` deve ser: (a) injetado no system prompt, (b) anexado programaticamente no evento `done`, ou (c) aceito como dependência do LLM no MVP?
**Impacto:** Define o mecanismo de conformidade LGPD no caminho de maior uso (frontend usa SSE).

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 7 — Guardrail de saída pós-hoc no streaming (P-35)

**Contexto:** `check_output` roda **depois** de os tokens já terem sido transmitidos no SSE; conteúdo proibido pode chegar ao cliente antes da supressão (`orchestrator.py`, evento `token` yield antes do `check_output`).
**Spec afetada:** [`_reversa_sdd/conversations/stream-sse/design.md` Riscos] [`_reversa_sdd/ai_engine/design.md`]
**Pergunta:** O guardrail de saída no stream é aceito como risco no MVP (documentado), ou exige mitigação (buffer + checagem por janela de tokens, ou cortar o stream no bloqueio)?
**Impacto:** Permanece 🔴 documentado, ou vira requisito de segurança com desenho de mitigação.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 8 — Turno órfão no streaming (P-36/P-20)

**Contexto:** Falha de provider, desconexão ou exceção após persistir a USER deixam mensagem sem resposta ASSISTANT e sem estado `pending/failed`/idempotência/retry — tanto no stream quanto no REST (turno parcialmente persistido).
**Spec afetada:** [`_reversa_sdd/conversations/stream-sse/design.md` Riscos] [`_reversa_sdd/conversations/post-message/design.md`] [`_reversa_sdd/state-machines.md`]
**Pergunta:** O MVP precisa de estado de turno (`pending/failed`) + idempotência/retry, ou o modelo atual (USER persistida + falha visível) é aceitável?
**Impacto:** Adiciona máquina de estados de turno, ou documenta a limitação como aceita.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 9 — Sem throttle no streaming (P-19)

**Contexto:** `@throttle_classes([ChatThrottle])` existe apenas em `post_message`; `stream` (caminho principal do frontend, mais caro) não tem limite de requisição (`views.py:105` vs `views.py:120`).
**Spec afetada:** [`_reversa_sdd/conversations/requirements.md` RN-13/RNF] [`_reversa_sdd/conversations/stream-sse/requirements.md` RN-06]
**Pergunta:** O `stream` deve receber throttle no MVP (ex.: mesmo `ChatThrottle` 10/min, ou limite próprio para SSE)?
**Impacto:** Adiciona regra de rate-limit ao contrato do stream, ou permanece 🔴 de custo/segurança.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 10 — KB com acesso cruzado entre usuários (P-25)

**Contexto:** `upload`/`list`/`status`/`delete` de documentos usam `IsAuthenticated` (qualquer autenticado lê/deleta documentos de terceiros, pois buscam por `pk` sem escopo ao `uploaded_by`); apenas `metrics` exige `IsAdminRole`. A KB alimenta as respostas do chat — vetor de conteúdo.
**Spec afetada:** [`_reversa_sdd/rag/requirements.md` RN-09/RNF] [`_reversa_sdd/rag/design.md`] [`_reversa_sdd/user-stories/gestao-conhecimento.md`]
**Pergunta:** A KB deve ser: (a) global e compartilhada (confirmar que qualquer autenticado pode alimentar), (b) escopada ao uploader (cada médico vê/deleta só os seus), ou (c) restrita a `IsAdminRole`?
**Impacto:** Define o modelo de permissão da base de conhecimento; muda contratos de status/delete.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 11 — Atomicidade Postgres ↔ ChromaDB (P-38)

**Contexto:** Ingestão faz `coll.add(...)` e depois `doc.status=INDEXED; doc.save()`; delete apaga do Chroma e depois o registro SQL — falha intermediária deixa vetores órfãos ou registros órfãos, sem compensação/reconciliação.
**Spec afetada:** [`_reversa_sdd/rag/upload-ingest/design.md`] [`_reversa_sdd/rag/delete/design.md`]
**Pergunta:** No MVP aceita-se a eventual divergência (com documentação), ou exige-se compensação/job de reconciliação por `document_id`?
**Impacto:** Documenta o risco aceito, ou adiciona saga/outbox ao desenho do RAG.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 12 — `patient_created` sempre False (R43)

**Contexto:** O contrato SSE expõe `patient_created`, mas `getattr(result, "_patient_just_created", False)` lê atributo inexistente em `CaptureResult` (`user_data_capture.py:124`) — nunca reporta `True`. Frontend não distingue paciente criado vs existente.
**Spec afetada:** [`_reversa_sdd/ai_engine/design.md`] [`_reversa_sdd/domain.md` R43]
**Pergunta:** `patient_created` deve ser corrigido (a flag real preenchida) no MVP, ou o campo permanece como placeholder documentado?
**Impacto:** Correção de código ou ajuste do contrato SSE.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 13 — Services de paciente sem validação de tenant (P-28)

**Contexto:** `ensure_or_create_patient`/`resolve_patient_dob` não verificam que a conversa e o médico pertencem ao mesmo tenant; o `doctor_id` é recebido como parâmetro sem cruzamento com `conversation.doctor_id` (`apps/patients/services/patient.py`).
**Spec afetada:** [`_reversa_sdd/patients/ensure-or-create/requirements.md`] [`_reversa_sdd/patients/resolve-dob/requirements.md`] [`_reversa_sdd/domain.md` R8]
**Pergunta:** Os services de paciente devem validar o tenant (conversa ↔ médico) no MVP, ou o fluxo atual (caller confiável = orquestrador) é suficiente?
**Impacto:** Adiciona checagem de ownership no service layer, ou documenta a confiança no caller.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 14 — Deduplicação não transacional e merge indefinido (P-30/P-31)

**Contexto:** A dedup por nome+DOB não roda em transação e não coincide com a constraint parcial `(doctor, first_name, birth_date)`; o merge dos dados do paciente tentativo no paciente existente não é especificado (dados parciais podem divergir).
**Spec afetada:** [`_reversa_sdd/patients/resolve-dob/requirements.md`] [`_reversa_sdd/domain.md` R12]
**Pergunta:** A dedup deve ser atômica (transação) e o merge especificado no MVP, ou o comportamento atual é aceito com ressalvas?
**Impacto:** Endurece a regra de dedup ou documenta a limitação.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 15 — `persist_user_name` com usuário inexistente → 500 (P-39)

**Contexto:** `User.DoesNotExist` no service não tem mapeamento no handler (que retorna `None` → 500 padrão do Django); a spec atribuía 404 sem adaptador real.
**Spec afetada:** [`_reversa_sdd/accounts/persist-user-name/requirements.md`] [`_reversa_sdd/common/requirements.md` RN-03]
**Pergunta:** O contrato de `persist_user_name` para usuário inexistente deve ser: (a) `NOT_FOUND` 404 (capturar no service/orquestrador), (b) resultado nulo silencioso, ou (c) 500 (caso não ocorra na prática)?
**Impacto:** Fixa o código de erro da captura de nome.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 16 — Query params inválidos → 500 (P-32/P-33)

**Contexto:** `int(request.query_params.get("patient_id"))` e `int(request.query_params.get("page"))` lançam `ValueError` → 500; paginação manual não especifica entradas inválidas (`health_logs/views.py:31,34,93`; `conversations/views.py:64`).
**Spec afetada:** [`_reversa_sdd/health_logs/requirements.md`] [`_reversa_sdd/conversations/requirements.md`]
**Pergunta:** Entradas inválidas (não-numéricas) devem retornar 400 `VALIDATION_ERROR` no MVP, ou permanecem como 500 não contratado?
**Impacto:** Contratos de entrada das listagens ficam completos, ou permanece 🔴.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 17 — Código morto: `GuardrailBlockedError` e `IsOwner`

**Contexto:** `GuardrailBlockedError` (200) nunca é lançada — o orquestrador retorna `GenerateResult(blocked=True)`; `IsOwner` não é usada por nenhuma view (as views filtram por `doctor=request.user` diretamente).
**Spec afetada:** [`_reversa_sdd/common/requirements.md` RN-04/RF-03] [`_reversa_sdd/common/design.md`]
**Pergunta:** Manter como parte da spec (com nota de código morto) ou remover da spec para refletir o que existe?
**Impacto:** Spec fiel ao código (remove claims inexistentes) ou documenta a intenção futura.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 18 — Convenção de env violada no RAG

**Contexto:** `os.environ[...]` é lido direto em `vector_store.py:21`, `ingestion.py:34`, `retriever.py:14` (a convenção do projeto é ler env apenas em `settings.py`); `CHROMA_PERSIST_DIR` ausente → `KeyError` cru.
**Spec afetada:** [`_reversa_sdd/rag/design.md`] [`_reversa_sdd/rag/collection-singleton/design.md`]
**Pergunta:** Centralizar a leitura de env do RAG em `settings.py` é um ajuste a incorporar nas specs (recomendado), ou a divergência é aceita no MVP?
**Impacto:** Specs passam a exigir a convenção; o detalhe de implementação fica documentado como desvio.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 19 — `tokens_used` conta palavras no streaming (R39)

**Contexto:** No streaming, `tokens_used` é estimado por `len(text.split())` — palavras, não tokens reais; métricas de custo e auditoria ficam imprecisas (`orchestrator.py:332`).
**Spec afetada:** [`_reversa_sdd/ai_engine/design.md`] [`_reversa_sdd/domain.md` R39]
**Pergunta:** A estimativa por palavras é aceita no MVP (documentada), ou exige contagem real de tokens via SDK do provider?
**Impacto:** Mantém nota de imprecisão ou adiciona requisito de métrica precisa.

**Resposta:** <!-- preencha aqui -->

---

## Pergunta 20 — Catch-alls mascarando erros

**Contexto:** `except Exception` em `generate_stream` rotula qualquer erro como `LLM_PROVIDER_ERROR` (`orchestrator.py:301-303`); `extract_with_llm` engole qualquer erro como `None` silencioso (`data_extraction_llm.py:70`); ingestão rotula tudo como falha de indexação (`ingestion.py:66-70`).
**Spec afetada:** [`_reversa_sdd/ai_engine/design.md`] [`_reversa_sdd/rag/upload-ingest/design.md`]
**Pergunta:** Deve-se distinguir as classes de erro (provider vs interno) no MVP, ou os catch-alls genéricos são aceitos com nota?
**Impacto:** Especifica categorização de erros, ou documenta a limitação de observabilidade.

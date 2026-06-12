# Epic 5.2 — RAG Final

> **Objetivo:** Interface para gerenciar a base de conhecimento + testes da camada RAG.
> **Pré-requisito:** Epic 5.1 concluído (vector store, ingestão e retriever funcionando).
> Referência: [TASKS.md](../TASKS.md) · [epic-5-rag.md](epic-5-rag.md) (detalhes técnicos completos)
>
> **Atualização (2026-05-31):** A base de conhecimento é uma coleção **compartilhada** (`mediclaw_kb`). A curadoria deixou de ser exclusiva de admin — qualquer usuário autenticado pode subir/listar/remover documentos. Os endpoints mantêm o prefixo `/api/v1/admin/knowledge/` por compatibilidade, mas a permissão passou de `IsAdminRole` para `IsAuthenticated`.

---

## Story 5.2.1 — Endpoints de Conhecimento

- [x] `POST /api/v1/admin/knowledge/upload` — multipart, ≤ 10 MB, tipos `pdf/md/txt`
- [x] `GET /api/v1/admin/knowledge` — lista paginada de documentos
- [x] `GET /api/v1/admin/knowledge/{id}/status` — status e erro do documento
- [x] `DELETE /api/v1/admin/knowledge/{id}` — remove documento e seus chunks do Chroma
- [x] Permission `IsAuthenticated` em todos os endpoints (era `IsAdminRole`)
- [x] DELETE em doc `PROCESSING` retorna 409

## Story 5.2.2 — Validações de Upload

- [ ] Rejeita arquivo ausente → 400
- [ ] Rejeita arquivo > 10 MB → 400 (`FILE_TOO_LARGE`)
- [ ] Rejeita mimetype inválido → 400 (`INVALID_FILE_TYPE`)
- [ ] Registra `KB_UPLOAD` e `KB_DELETE` no audit log

## Story 5.2.3 — Testes obrigatórios

- [x] `test_upload_txt_returns_indexed_status`
- [x] `test_upload_rejects_oversize`
- [x] `test_upload_rejects_invalid_mimetype`
- [x] `test_delete_document_removes_from_chroma`
- [x] `test_delete_processing_document_returns_409`
- [x] `test_non_admin_can_upload` (curadoria compartilhada)
- [x] `test_anonymous_upload_returns_401`

---

## Critérios de Aceite

- [x] Upload PDF/MD/TXT via API gera `KnowledgeDocument` com `status=INDEXED`
- [x] DELETE remove os chunks do Chroma (verificável via `coll.count()`)
- [x] Usuário autenticado (qualquer role) pode curar a base; anônimo recebe 401
- [x] Testes obrigatórios passando

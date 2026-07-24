# Epic 9 — RAG Segmentado por Conta (Pós-MVP)

> **Fase:** Pós-MVP / Evolução. Não faz parte do escopo aprovado no [PRD.md](../PRD.md) v1.0.
> Referência: [TASKS §Epic 9](../TASKS.md#epic-9--rag-segmentado-por-conta-pós-mvp) · epic irmão no frontend: [react-painel epic-8-org-admin.md](../../../react-painel/specs/epics/epic-8-org-admin.md)
> **Status:** Planejado, não iniciado.

---

## Problema

Hoje **toda a aplicação consulta uma única coleção global no ChromaDB** (`COLLECTION_NAME = "mediclaw_kb"`, ver `apps/rag/vector_store.py::get_collection()`). Qualquer documento indexado por qualquer usuário autenticado fica visível para todos os outros (curadoria foi aberta a `IsAuthenticated` no Epic 5.2, ver nota de 2026-05-31 em `epic-5.2-rag-final.md`). Não existe conceito de propriedade, equipe ou organização sobre a base de conhecimento.

Isso é aceitável para o MVP acadêmico (base única, poucos usuários de teste), mas bloqueia dois cenários:

1. **Privacidade entre profissionais independentes** — um médico não deveria ver/consultar os documentos indexados por outro médico que não tem relação com ele.
2. **Venda B2B para clínicas/empresas** — uma clínica quer que sua equipe compartilhe uma base de conhecimento própria, isolada de outras clínicas clientes, com um admin da própria organização controlando quem vê o quê.

## Objetivo

Introduzir isolamento de RAG por conta em duas etapas incrementais, sem quebrar o fluxo atual de single-tenant.

## Dependências

- E2 (Auth & Users — `User`, `role`, `IsAdminRole`)
- E5.1/E5.2 (RAG — `vector_store.py`, `retriever.py`, `KnowledgeDocument`)
- E8 (Patient Management — padrão de FK por dono já estabelecido com `Patient.doctor`)

---

## Etapa 1 — Isolamento por usuário

Cada usuário passa a ter sua própria partição de dados vetoriais. Duas abordagens possíveis (decidir na implementação, ambas compatíveis com Chroma):

**Opção A — metadata filter (recomendada para MVP desta etapa):** mantém uma única coleção física, mas toda escrita e leitura passa a filtrar por `owner_id`.

```python
# apps/rag/vector_store.py — sem mudança estrutural, mesma coleção física
def get_collection():
    ...  # inalterado

# apps/rag/ingestion.py — ingest() passa a receber owner_id
def ingest(document: KnowledgeDocument, file_bytes: bytes, owner_id: int) -> None:
    ...
    metadatas = [
        {"document_id": str(document.id), "title": document.title,
         "chunk_index": i, "owner_id": str(owner_id)}
        for i in range(len(chunks))
    ]
    coll.add(ids=ids, documents=chunks, embeddings=vectors, metadatas=metadatas)

# apps/rag/retriever.py — search() passa a exigir owner_id
def search(query: str, owner_id: int, k: int = 5, min_score: float = 0.75) -> list[dict]:
    coll = get_collection()
    if coll.count() == 0:
        return []
    qvec = _get_embeddings().embed_query(query)
    res = coll.query(
        query_embeddings=[qvec], n_results=k,
        where={"owner_id": str(owner_id)},
        include=["documents", "metadatas", "distances"],
    )
    ...
```

**Opção B (alternativa futura, se performance exigir):** uma coleção Chroma por usuário (`f"mediclaw_kb_{user_id}"`), evitando `where` em coleções muito grandes. Mais custosa operacionalmente (Chroma limita número de coleções por client de forma eficiente até a casa dos milhares); só migrar se a Opção A mostrar gargalo real.

**Mudanças de modelo:**

```python
# apps/rag/models.py
class KnowledgeDocument(models.Model):
    ...
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="knowledge_documents")
    # substitui/complementa uploaded_by; owner define o escopo de busca
```

**Orquestrador:** `apps/ai_engine/orchestrator.py` passa `doctor_id` (já disponível na chamada) para `retriever.search()`.

**Migração de dados existentes:** documentos já indexados sem `owner_id` continuam globais até serem reindexados, ou recebem um `owner_id` de "sistema" (primeiro admin) numa migration de dados — decidir conforme volume real em produção no momento da implementação.

## Etapa 2 — Multi-tenancy para venda B2B

Introduz a entidade `Organization` e um admin escopado por organização (não mais só o `IsAdminRole` global existente em `apps/common/permissions.py`).

```python
# apps/organizations/models.py (novo app)
class Organization(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class OrganizationMembership(models.Model):
    ROLE_CHOICES = [("MEMBER", "MEMBER"), ("ORG_ADMIN", "ORG_ADMIN")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="MEMBER")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_membership")]
```

```python
# apps/common/permissions.py — nova permission, ao lado de IsAdminRole/IsOwner
class IsOrgAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.org_memberships.filter(role="ORG_ADMIN").exists()
        )
```

`KnowledgeDocument.owner_id` passa a poder representar tanto um usuário individual quanto uma organização (`scope_type: "USER" | "ORGANIZATION"`, `scope_id`), e `retriever.search()` recebe o escopo resolvido a partir do usuário logado (usuário sem organização busca só seu próprio `owner_id`; usuário com organização busca pelo `owner_id` da organização, compartilhado entre a equipe).

**Endpoints novos (admin de organização):**

```python
# apps/organizations/urls.py
urlpatterns = [
    path("", list_organizations),                        # GET  — IsAdminRole (global)
    path("<int:org_id>/members", list_members),           # GET  — IsOrgAdmin ou IsAdminRole
    path("<int:org_id>/members", add_member),              # POST — IsOrgAdmin ou IsAdminRole
    path("<int:org_id>/members/<int:user_id>", remove_member),  # DELETE
]
```

## Critérios de Aceite

**Etapa 1:**
- [ ] `KnowledgeDocument` tem `owner`; `search()` exige `owner_id` e nunca retorna chunks de outro dono
- [ ] Upload sem indicar dono explícito usa `request.user` automaticamente
- [ ] Teste: usuário A não recupera nenhum chunk indexado pelo usuário B
- [ ] Documentos legados (sem `owner_id`) tratados de forma explícita (não vazam silenciosamente para todo mundo)

**Etapa 2:**
- [ ] `Organization` e `OrganizationMembership` criados com migrations
- [ ] `IsOrgAdmin` bloqueia usuários fora da organização (403)
- [ ] Usuário de uma organização busca no escopo compartilhado da organização, não apenas no próprio
- [ ] Admin global (`IsAdminRole`) continua enxergando/gerenciando todas as organizações

## Testes obrigatórios

```python
# tests/rag/test_ownership.py
def test_search_only_returns_own_documents(): ...
def test_search_excludes_other_users_documents(): ...
def test_upload_sets_owner_to_request_user(): ...

# tests/organizations/test_membership.py
def test_org_admin_can_manage_members(): ...
def test_non_member_cannot_access_org_endpoints(): ...
def test_member_search_scoped_to_organization(): ...
```

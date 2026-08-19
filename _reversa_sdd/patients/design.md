# Patients, Design Técnico

> Contrato operacional de **COMO** a unit `patients` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

### Endpoints HTTP

| Método | Caminho | Entrada | Saída | Status codes | Permissão |
|--------|---------|---------|-------|--------------|-----------|
| GET | `/api/v1/patients/` | `page: int` (default 1) | `{results: PatientList[], count: int, next: string\|null}` | 200, 401 | `IsAuthenticated` |
| GET | `/api/v1/patients/<patient_id>/` | `patient_id: int` | `PatientDetail` | 200, 401, 404 | `IsAuthenticated` |
| PATCH | `/api/v1/patients/<patient_id>/` | subset de campos do Patient | `PatientList` | 200, 400, 401, 404 | `IsAuthenticated` |
| DELETE | `/api/v1/patients/<patient_id>/` | — | `204 No Content` | 204, 401, 404 | `IsAuthenticated` |

**Formato `PatientList`**: `{id, first_name, birth_date, biological_sex, height_cm, conversation_count, last_seen_at, latest_weight_kg, created_at, updated_at}`. 🟢
**Formato `PatientDetail`**: `PatientList` + `{weight_logs[], sleep_logs[], activity_logs[], nutrition_notes[], conversations[]}` (conversas ordenadas por `-updated_at`). 🟢
**Pagination manual**: `PAGE_SIZE = 20`, via `offset = (page-1)*20` e slice no queryset; `next` é a query string `?page=N+1`. 🟢

### Funções / classes

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `_annotate_patients` | `(qs: QuerySet[Patient]) -> QuerySet[Patient]` | QS anotado | Adiciona `conversation_count`, `last_seen_at`, `latest_weight_kg` |
| `list_patients` | `(request: Request) -> Response` | paginação | Filtra `doctor=request.user` |
| `patient_detail` | `(request: Request, patient_id: int) -> Response` | detalhe | GET/PATCH/DELETE escopado ao dono |
| `ensure_or_create_patient` | `(conversation_id: int, doctor_id: int, first_name: str) -> Patient` | `Patient` | Cria/atualiza paciente da conversa (captura via chat) |
| `resolve_patient_dob` | `(conversation_id: int, doctor_id: int, birth_date: date) -> Patient \| None` | `Patient \| None` | Dedup por nome+DOB; `None` se conversa sem paciente |

## Fluxo Principal

### 1. Listagem (`GET /api/v1/patients/`)

1. Filtra `Patient.objects.filter(doctor=request.user)`. (`apps/patients/views.py:41`) 🟢
2. `_annotate_patients` adiciona: `conversation_count` (Count das conversas com `deleted_at__isnull=True`), `last_seen_at` (Max de `conversations__updated_at` filtrando não-deletadas) e `latest_weight_kg` (Subquery do peso mais recente por paciente). (`apps/patients/views.py:16-33`) 🟢
3. Paginação manual: `count = qs.count()`, `items = qs[offset:offset+PAGE_SIZE]`, `next = "?page=N+1"` se houver. (`apps/patients/views.py:39-51`) 🟢
4. Serializa com `PatientListSerializer` e retorna `{results, count, next}`. 🟢

### 2. Detalhe / Atualização / Deleção (`GET|PATCH|DELETE /api/v1/patients/<id>/`)

1. `_annotate_patients(Patient.objects.filter(doctor=request.user)).get(pk=patient_id)` — busca já escopada ao dono; `Patient.DoesNotExist` → `AppError("NOT_FOUND", ..., 404)`. (`apps/patients/views.py:57-62`) 🟢
2. **GET:** `PatientDetailSerializer` inclui `weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes` (read-only) e `conversations` via `get_conversations` (`obj.conversations.order_by("-updated_at")`). (`apps/patients/serializers.py:63-81`) 🟢
3. **PATCH:** `PatientListSerializer(patient, data=request.data, partial=True)` → valida → `save()`. Read-only fields (`id`, timestamps, anotações) são ignorados. (`apps/patients/views.py:67-71`) 🟢
4. **DELETE:** `patient.delete()` → 204. Conversas mantêm a FK com `SET_NULL`. (`apps/patients/views.py:73-75`) 🟢

### 3. Captura de paciente via chat (`ensure_or_create_patient`)

1. Busca `Conversation` por `pk`. (`apps/patients/services/patient.py:20`) 🟢
2. Se `conv.patient_id` já existe e `patient.first_name` está vazio → preenche apenas o nome (`update_fields=["first_name","updated_at"]`) e retorna. (`apps/patients/services/patient.py:22-28`) 🟢
3. Senão, cria `Patient(doctor_id, first_name.strip())`, vincula em `conv.patient` e grava `conv.title = first_name.strip()[:120]`. (`apps/patients/services/patient.py:30-36`) 🟢
4. `logger.debug("patient_created", patient_id=..., conversation_id=...)`. (`apps/patients/services/patient.py:37-41`) 🟢

### 4. Resolução de DOB com dedup (`resolve_patient_dob`)

1. Busca conversa; se `conv.patient_id is None` → `None`. (`apps/patients/services/patient.py:53-55`) 🟢
2. Procura paciente existente com `doctor_id`, `first_name__iexact` e `birth_date` igual, excluindo o tentativo. (`apps/patients/services/patient.py:59-67`) 🟢
3. Se encontrado: re-vincula a conversa ao paciente existente; deleta o tentativo **apenas se não tiver** `weight_logs`, `sleep_logs`, `activity_logs` nem `nutrition_notes`. (`apps/patients/services/patient.py:69-89`) 🟢
4. Se não encontrado: grava `birth_date` no tentativo (`update_fields=["birth_date","updated_at"]`). (`apps/patients/services/patient.py:91-94`) 🟢

## Fluxos Alternativos

- **[Paciente fora do escopo]:** busca escopada a `doctor=request.user` → id de outro médico cai em `DoesNotExist` → 404 `NOT_FOUND` (não vaza existência). 🟢
- **[Página vazia]:** `items` vazio → `{results: [], count: N, next: null}`. 🟢
- **[Paciente tentativo com dados próprios]:** no dedup, se o tentativo tem logs/refeições, ele **não** é deletado — a conversa migra para o existente e o tentativo permanece órfão. 🟡
- **[Conversa sem paciente na captura de DOB]:** `resolve_patient_dob` retorna `None` sem efeito. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.health_logs.models.WeightLog` | Anotação de `latest_weight_kg` | Subquery em `_annotate_patients` (`views.py:18-22`) |
| `apps.conversations.models.Conversation` | Vínculo paciente↔conversa | FK `patient` (`SET_NULL`), `deleted_at` para contagem; usada nos services de captura |
| `apps.common.exceptions.AppError` | Erro `NOT_FOUND` com envelope | `views.py:62` |
| `apps.common.logging_config.get_logger` | Logs estruturados dos services | `services/patient.py:3-7` |
| `django.contrib.auth` + `settings.AUTH_USER_MODEL` | Dono do paciente | FK `doctor` (`models.py:9-13`) |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Paginação manual via slice + `next` como query string (não `PageNumberPagination` do DRF) | `apps/patients/views.py:39-51` | 🟢 |
| Anotação de peso mais recente via `Subquery` (evita N+1 na listagem) | `apps/patients/views.py:18-22` | 🟢 |
| Contagem/última atividade excluem conversas soft-deletadas | `apps/patients/views.py:25-31` | 🟢 |
| Unicidade no banco via constraint parcial `(doctor, first_name, birth_date)` quando DOB presente | `apps/patients/models.py:24-30` | 🟢 |
| Dedup por `first_name__iexact` + DOB exata por médico (não usa normalização de nome) | `apps/patients/services/patient.py:59-67` | 🟢 |
| Um paciente tentativo por conversa; mesclagem só na captura de DOB | `apps/patients/services/patient.py:22-42,45-94` | 🟢 |
| `patient` FK em `Conversation` com `SET_NULL` (deletar paciente preserva conversas) | `apps/conversations/models.py:18-24` | 🟢 |
| Detalhe embute logs/refeições/conversas via serializers aninhados (não endpoints separados) | `apps/patients/serializers.py:63-81` | 🟢 |
| Access control por escopo de queryset (não por object permission) | `apps/patients/views.py:41,58` | 🟢 |

## Estado Interno

Modelo `Patient`:

| Campo | Tipo | Observação |
|-------|------|------------|
| `id` | PK auto | — |
| `doctor` | FK `AUTH_USER_MODEL` (`CASCADE`, `related_name="patients"`) | Dono; base do escopo de acesso |
| `first_name` | `CharField(120)`, obrigatório | Nome do paciente; alvo da captura via chat |
| `birth_date` | `DateField(null=True)` | Usado no dedup por nome+DOB |
| `biological_sex` | `CharField(choices=M/F/OTHER, null=True)` | Dado sensível (LGPD) |
| `height_cm` | `PositiveSmallIntegerField(null=True)` | — |
| `created_at` / `updated_at` | auto | Ordenação padrão: `-created_at` |

Constraints: `unique_patient_name_dob_per_doctor` (parcial); índices `(doctor, first_name)` e `(doctor, -created_at)`. 🟢

## Observabilidade

- `logger.debug("patient_created", patient_id=..., conversation_id=...)` na criação via chat. (`apps/patients/services/patient.py:37-41`) 🟢
- `logger.debug("patient_merged", tentative_patient_id=..., existing_patient_id=..., conversation_id=...)` no dedup. (`apps/patients/services/patient.py:83-88`) 🟢
- Sem logs de acesso CRUD HTTP (listagem/detalhe) e sem métricas. 🟡

## Riscos e Lacunas

- 🔴 Gap registrado pelo Arquiteto: `patient_created` observado "sempre False" — validar se o `get_logger` estruturado emite eventos `debug` de fato (possível configuração de nível de log), ou se há outra flag `patient_created` que nunca é setada no fluxo de captura.
- 🟡 No dedup com paciente tentativo **com dados**, o tentativo não é deletado e fica órfão (sem re-vínculo) — fluxo incompleto de mesclagem de dados.
- 🟡 `PAGE_SIZE` fixo em 20 no código (sem query param); validar requisito de paginação dinâmica.
- 🟡 Dedup por `iexact` + DOB não considera variações de nome (abreviações, typos) — limitação conhecida do MVP.
- 🟡 Sem throttling explícito na listagem/detalhe (checklist do projeto prevê anon+user).

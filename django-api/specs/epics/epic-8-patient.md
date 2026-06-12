# Epic 8 — Patient Management

> **Objetivo:** Introduzir a entidade `Patient` para separar dados do médico (User) dos dados do paciente atendido. Cada conversa pertence a um único paciente, identificado por nome + data de nascimento. Dados biométricos (health logs) e dados de perfil migram de `User/Profile` para `Patient`.
> **Pré-requisito:** E1–E6 completos.
> **Breaking change:** Migrations alteram FKs existentes — ver Story 8.1.

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| App de destino | Novo app `apps/patients/` | Entidade com API própria; separação limpa |
| Profile | Removido de `accounts`; campos migram para `Patient` | Profile pertence ao paciente, não ao médico |
| Health logs FK | `user` → `patient` (FK Patient) | Logs biométricos são do paciente |
| Conversation FK | Adiciona `patient` (nullable); renomeia `user` → `doctor` | Conversa é do médico, mas vinculada a um paciente |
| Soft delete | `Conversation.deleted_at` (DateTimeField, null) | Dados médicos não são destruídos — ficam ocultos |
| Deduplicação | Nome + data de nascimento por médico | Mesmo paciente físico reconhecido em consultas futuras |

---

## Story 8.1 — Novo app `patients` e migrations

### Novo model `Patient`

```python
# apps/patients/models.py
from django.db import models
from django.conf import settings

SEX_CHOICES = [("M", "Masculino"), ("F", "Feminino"), ("OTHER", "Outro")]

class Patient(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patients",
    )
    first_name = models.CharField(max_length=120)
    birth_date = models.DateField(null=True, blank=True)
    biological_sex = models.CharField(max_length=10, choices=SEX_CHOICES, null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Unicidade: mesmo médico não pode ter dois pacientes com mesmo nome E mesma data de nascimento
        # Permite: mesmo nome sem DOB (DOB ainda não capturado)
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "first_name", "birth_date"],
                condition=models.Q(birth_date__isnull=False),
                name="unique_patient_name_dob_per_doctor",
            )
        ]
        indexes = [
            models.Index(fields=["doctor", "first_name"]),
            models.Index(fields=["doctor", "-created_at"]),
        ]
        ordering = ["-created_at"]
```

### Modificações em models existentes

```python
# apps/conversations/models.py — alterações
class Conversation(models.Model):
    doctor = models.ForeignKey(           # renomeado de 'user'
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    patient = models.ForeignKey(          # novo campo
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    title = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete

    class Meta:
        indexes = [
            models.Index(fields=["doctor", "-updated_at"]),
            models.Index(fields=["patient", "-updated_at"]),
        ]
        ordering = ["-updated_at"]

# apps/health_logs/models.py — FK user → patient em TODOS os modelos
class WeightLog(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="weight_logs")
    # ... demais campos inalterados

class SleepLog(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="sleep_logs")
    # ...

class ActivityLog(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="activity_logs")
    # ...

class NutritionNote(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="nutrition_notes")
    # ...
```

### `accounts/models.py` — remoção do Profile

```python
# Profile é removido. Campos birth_date, biological_sex, height_cm agora residem em Patient.
# User mantém apenas: email, role, accepted_terms_at, first_name
```

### Strategy de migration

1. `makemigrations patients` — cria `Patient`
2. `makemigrations accounts` — remove `Profile`
3. `makemigrations health_logs` — troca FK `user → patient`
4. `makemigrations conversations` — renomeia `user → doctor`, adiciona `patient`, adiciona `deleted_at`
5. Migration de dados (RunPython):
   - Para cada `User` existente que tenha dados em logs → criar um `Patient` genérico (first_name=user.first_name, doctor=user) e re-apontar os logs
   - Para cada `Conversation` existente → setar `doctor=user` (renomear coluna)

---

## Story 8.2 — API de Pacientes

### Serializers

```python
# apps/patients/serializers.py

class PatientListSerializer(serializers.ModelSerializer):
    conversation_count = serializers.IntegerField(read_only=True)
    last_seen_at = serializers.DateTimeField(read_only=True)  # annotated
    latest_weight_kg = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2, allow_null=True)

    class Meta:
        model = Patient
        fields = ["id", "first_name", "birth_date", "biological_sex", "height_cm",
                  "conversation_count", "last_seen_at", "latest_weight_kg", "created_at"]


class PatientDetailSerializer(PatientListSerializer):
    weight_logs = WeightLogSerializer(many=True, read_only=True)
    sleep_logs = SleepLogSerializer(many=True, read_only=True)
    activity_logs = ActivityLogSerializer(many=True, read_only=True)
    nutrition_notes = NutritionNoteSerializer(many=True, read_only=True)
    conversations = ConversationSummarySerializer(many=True, read_only=True)

    class Meta(PatientListSerializer.Meta):
        fields = PatientListSerializer.Meta.fields + [
            "weight_logs", "sleep_logs", "activity_logs", "nutrition_notes", "conversations"
        ]
```

### ViewSet

```python
# apps/patients/views.py
class PatientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        return (
            Patient.objects
            .filter(doctor=self.request.user)
            .annotate(
                conversation_count=Count("conversations", filter=Q(conversations__deleted_at__isnull=True)),
                last_seen_at=Max("conversations__updated_at", filter=Q(conversations__deleted_at__isnull=True)),
                latest_weight_kg=Subquery(
                    WeightLog.objects.filter(patient=OuterRef("pk"))
                    .order_by("-measured_at").values("value_kg")[:1]
                ),
            )
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PatientDetailSerializer
        return PatientListSerializer
```

### Endpoints

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| `GET` | `/api/v1/patients/` | Lista pacientes do médico com `conversation_count`, `last_seen_at`, `latest_weight_kg` | Bearer |
| `GET` | `/api/v1/patients/{id}/` | Detalhe: perfil + logs + conversas | Bearer |
| `PATCH` | `/api/v1/patients/{id}/` | Atualiza `first_name`, `birth_date`, `biological_sex`, `height_cm` | Bearer |
| `DELETE` | `/api/v1/patients/{id}/` | Hard delete (cascade: logs + conversas hard-deletadas) | Bearer |

---

## Story 8.3 — Soft Delete em Conversations

### Comportamento

- `DELETE /api/v1/conversations/{id}/` → seta `deleted_at = now()` (não apaga)
- Todos os querysets de Conversation usam `filter(deleted_at__isnull=True)` por padrão
- `GET /api/v1/conversations/` — lista somente não-deletadas
- `GET /api/v1/conversations/{id}/` — 404 se `deleted_at` preenchido
- Hard delete só ocorre como cascade ao deletar um `Patient`

### Manager customizado

```python
class ConversationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Conversation(models.Model):
    objects = ConversationManager()
    all_objects = models.Manager()  # para admin / admin tasks
    # ...
```

---

## Story 8.4 — Captura de Dados → Patient

### Interface pública modificada

```python
# apps/ai_engine/services/user_data_capture.py

def capture_from_message(conversation_id: int, doctor_id: int, text: str) -> CaptureResult:
    """
    Captura dados da mensagem e salva no Patient vinculado à conversa.
    Cria/atualiza Patient conforme nome e DOB são extraídos.
    """
```

> **Assinatura anterior:** `capture_from_message(user_id: int, text: str)`
> **Nova assinatura:** `capture_from_message(conversation_id: int, doctor_id: int, text: str)`

### Fluxo interno

```
1. Extrai dados (regex + LLM) — sem mudança

2. Se nome extraído:
   └─▶ ensure_or_create_patient(doctor_id, conversation_id, first_name)
         ├── Busca Patient(doctor=doctor, first_name__iexact=nome) sem DOB confirmado
         ├── Se não existe → cria Patient(doctor, first_name, birth_date=None)
         └── Vincula Conversation.patient = patient (se ainda null)

3. Se birth_date extraída E patient já existe na conversa:
   └─▶ resolve_patient_dob(conversation, birth_date)
         ├── Busca Patient(doctor, first_name=atual, birth_date=DOB)
         ├── Se encontrou outro paciente → re-vincula conversa ao existente
         │    └── deleta patient tentativo sem outros dados
         └── Se não → atualiza patient.birth_date = DOB

4. Salva health data no patient da conversa:
   └─▶ WeightLog(patient=conversation.patient, ...) etc.
```

### `CaptureResult` — campos adicionados

```python
class CaptureResult(BaseModel):
    # ... campos existentes ...
    patient_id: int | None = None
    patient_created: bool = False
```

### Evento SSE `done` — campos adicionados

```json
{
  "type": "done",
  "tokens_used": 142,
  "blocked": false,
  "patient_id": 7,
  "patient_created": true,
  "onboarding_mode": "focus",
  "missing_basics": { "name": false, "profile": ["birth_date"], "weight_log": true },
  "data_capture": { "saved": {...}, "errors": [], "still_missing": {...} }
}
```

---

## Story 8.5 — Conversas retornam dados do Patient

### `ConversationSerializer` atualizado

```python
class PatientSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["id", "first_name", "birth_date"]

class ConversationSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "title", "patient", "created_at", "updated_at"]
```

---

## Story 8.6 — Testes

### Cobertura mínima

```
tests/patients/
├── test_patient_crud.py
│   ├── test_list_patients_own_only()
│   ├── test_retrieve_patient_with_logs()
│   ├── test_patch_patient_fields()
│   └── test_delete_patient_cascades_logs()
├── test_patient_dedup.py
│   ├── test_create_patient_on_name_capture()
│   ├── test_resolve_existing_patient_on_dob_match()
│   ├── test_new_patient_on_dob_mismatch()
│   └── test_same_name_different_doctor_not_deduped()
└── test_soft_delete.py
    ├── test_delete_conversation_sets_deleted_at()
    ├── test_deleted_conversation_not_in_list()
    └── test_deleted_conversation_returns_404()
```

---

## Critérios de Aceite da Epic

- [ ] `Patient` model existe em `apps/patients/` com constraints de unicidade (nome+DOB por médico)
- [ ] `Profile` removido; campos migrados para `Patient`
- [ ] Health logs (WeightLog, SleepLog, ActivityLog, NutritionNote) FK apontam para `Patient`
- [ ] `Conversation.doctor` (renomeado de `user`) + `Conversation.patient` (nullable) + `Conversation.deleted_at`
- [ ] `DELETE /api/v1/conversations/{id}/` faz soft delete (seta `deleted_at`)
- [ ] `GET /api/v1/conversations/` não retorna conversas soft-deletadas
- [ ] `GET /api/v1/patients/` lista apenas pacientes do médico autenticado
- [ ] `GET /api/v1/patients/{id}/` retorna detalhe com logs e conversas
- [ ] `capture_from_message` cria/resolve Patient e salva health logs no Patient
- [ ] Evento SSE `done` inclui `patient_id` e `patient_created`
- [ ] `ConversationSerializer` inclui `patient: {id, first_name}`
- [ ] Migration com RunPython preserva dados existentes
- [ ] Testes passando: CRUD de pacientes + deduplicação + soft delete

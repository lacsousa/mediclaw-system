# Dicionário de Dados — MediClaw (Backend Django)

> Gerado pelo **Arqueólogo** em 2026-08-19.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Artefato transversal — entidades adicionadas conforme a escavação avança.

---

## Entidade: `User` (`accounts.User`)

**Tabela:** `accounts_user`
**Herda:** `django.contrib.auth.models.AbstractUser`
**Identificador de login:** `email` (`USERNAME_FIELD = "email"`)

### Campos próprios (não herdados)

| Campo | Tipo | Obrigatório | Default | Restrições | Descrição | Confiança |
|---|---|---|---|---|---|---|
| `username` | CharField(150) | Não | `""` (blank) | — | Herdado do AbstractUser; **não usado como login** (fica em branco) | 🟢 |
| `email` | EmailField(254) | Sim | — | `unique=True`; normalizado minúsculo | Login e identificador único do usuário | 🟢 |
| `role` | CharField(10) | Sim | `"USER"` | `choices=[USER, ADMIN]` | Papel do usuário (RBAC simples) | 🟢 |
| `accepted_terms_at` | DateTimeField | Não | `null` | — | Consentimento LGPD explícito (preenchido no cadastro) | 🟢 |

### Campos herdados de `AbstractUser` (relevantes)

| Campo | Tipo | Obrigatório | Default | Descrição | Confiança |
|---|---|---|---|---|---|
| `id` | BigAutoField | Sim | auto | PK | 🟢 |
| `password` | CharField(128) | Sim | — | Hash de senha (Django) | 🟢 |
| `first_name` | CharField(150) | Não | `""` | Nome/display name (mapeado de `name` no cadastro) | 🟢 |
| `last_name` | CharField(150) | Não | `""` | Sobrenome (não usado no MVP) | 🟢 |
| `is_active` | BooleanField | Sim | `True` | Login bloqueado se `False` (rejeitado com `INVALID_CREDENTIALS`) | 🟢 |
| `is_staff` | BooleanField | Sim | `False` | Acesso ao Django admin | 🟢 |
| `is_superuser` | BooleanField | Sim | `False` | Super privilégios | 🟢 |
| `date_joined` | DateTimeField | Sim | `now` | Data de criação | 🟢 |
| `last_login` | DateTimeField | Não | `null` | Último login | 🟢 |
| `groups` | M2M → `auth.Group` | Não | — | Grupos Django | 🟢 |
| `user_permissions` | M2M → `auth.Permission` | Não | — | Permissões Django | 🟢 |

### Relacionamentos recebidos (cascade de exclusão — LGPD)

O `User` é deletado em cascata via `Patient.doctor` e `Conversation.doctor`. Logs biométricos penduram no `Patient` (não no `User` direto):

| Origem | Campo FK | on_delete | Confiança |
|---|---|---|---|
| `patients.Patient` | `doctor` | CASCADE | 🟢 |
| `health_logs.WeightLog` | `patient` | CASCADE (transitivo via Patient) | 🟢 |
| `health_logs.SleepLog` | `patient` | CASCADE (transitivo via Patient) | 🟢 |
| `health_logs.ActivityLog` | `patient` | CASCADE (transitivo via Patient) | 🟢 |
| `health_logs.NutritionNote` | `patient` | CASCADE (transitivo via Patient) | 🟢 |
| `conversations.Conversation` | `doctor` | CASCADE | 🟢 |
| `conversations.Conversation` | `patient` | `SET_NULL` (null=True) — conversa sobrevive à exclusão do paciente, mas não do médico | 🟢 |
| `conversations.Message` | `conversation` | CASCADE | 🟢 |

> Cadeia LGPD: `User.delete()` → remove `Patient` (cascade) → remove logs biométricos e conversas do paciente; remove `Conversation` (via doctor) → remove `Message`. Dados sensíveis de saúde não ficam órfãos. 🟢

### Enums / constantes

| Nome | Valores | Local | Confiança |
|---|---|---|---|
| `User.ROLE_CHOICES` | `USER`, `ADMIN` | models.py:23 | 🟢 |
| `PASSWORD_RX` | `^(?=.*[A-Za-z])(?=.*\d).{8,}$` | serializers.py:6 | 🟢 |
| `WELCOME_CONVERSATION_TITLE` | `"Bem-vindo"` | conversations/services/welcome.py:7 | 🟢 |
| `WELCOME_METADATA_FLAG` | `"welcome"` | conversations/services/welcome.py:8 | 🟢 |

---

## Entidade: `Patient` (`patients.Patient`)

**Tabela:** `patients_patient`
**Donos:** vinculado a um `User` (médico) via `doctor`

### Campos

| Campo | Tipo | Obrigatório | Default | Restrições | Descrição | Confiança |
|---|---|---|---|---|---|---|
| `id` | BigAutoField | Sim | auto | PK | | 🟢 |
| `doctor` | FK → `accounts.User` | Sim | — | `on_delete=CASCADE`, `related_name="patients"` | Médico dono do paciente | 🟢 |
| `first_name` | CharField(120) | Sim | — | — | Nome (display principal do paciente) | 🟢 |
| `birth_date` | DateField | Não | `null` | — | DOB; parcial no `UniqueConstraint` | 🟢 |
| `biological_sex` | CharField(10) | Não | `null` | `choices=[M, F, OTHER]` | Sexo biológico | 🟢 |
| `height_cm` | PositiveSmallIntegerField | Não | `null` | — | Altura em cm | 🟢 |
| `created_at` | DateTimeField | Sim | `auto_now_add` | — | Criação | 🟢 |
| `updated_at` | DateTimeField | Sim | `auto_now` | — | Última atualização | 🟢 |

### Constraints e índices

| Tipo | Definição | Confiança |
|---|---|---|
| Unique (parcial) | `(doctor, first_name, birth_date)` **somente se** `birth_date IS NOT NULL` — nome `unique_patient_name_dob_per_doctor` | 🟢 |
| Index | `(doctor, first_name)` | 🟢 |
| Index | `(doctor, -created_at)` | 🟢 |

### Relacionamentos emitidos

| Campo | Alvo | on_delete | related_name | Confiança |
|---|---|---|---|---|
| `conversations` (reverse de `Conversation.patient`) | `conversations.Conversation` | `SET_NULL` (null=True) | `conversations` | 🟢 |
| `weight_logs` (reverse) | `health_logs.WeightLog` | CASCADE | `weight_logs` | 🟢 |
| `sleep_logs` (reverse) | `health_logs.SleepLog` | CASCADE | `sleep_logs` | 🟢 |
| `activity_logs` (reverse) | `health_logs.ActivityLog` | CASCADE | `activity_logs` | 🟢 |
| `nutrition_notes` (reverse) | `health_logs.NutritionNote` | CASCADE | `nutrition_notes` | 🟢 |

> Deletar paciente remove logs biométricos em cascata, mas conversas permanecem (`SET_NULL`). 🟢

### Serializers relacionados

| Serializer | Uso | Campos computados |
|---|---|---|
| `PatientListSerializer` | Lista/PATCH | `conversation_count`, `last_seen_at`, `latest_weight_kg` (read-only, anotados na view) |
| `PatientDetailSerializer` | Detalhe | Herda lista + `weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes`, `conversations` (via `get_conversations`) |
| `ConversationSummarySerializer` | Aninhado | `id`, `title`, `created_at`, `updated_at` |
| `WeightLogSerializer` / `SleepLogSerializer` / `ActivityLogSerializer` / `NutritionNoteSerializer` | Aninhados | Campos básicos de cada log |

---

## Entidade: `WeightLog` (`health_logs.WeightLog`)

**Tabela:** `health_logs_weightlog`
**Append-only** (REST expõe apenas GET/POST/DELETE)

| Campo | Tipo | Obrigatório | Restrições | Confiança |
|---|---|---|---|---|
| `id` | BigAutoField | Sim | PK | 🟢 |
| `patient` | FK → `patients.Patient` | Sim | `on_delete=CASCADE`, `related_name="weight_logs"` | 🟢 |
| `value_kg` | DecimalField(5,2) | Sim | validação: `20–400` (REST + chat) | 🟢 |
| `measured_at` | DateTimeField | Sim | não pode ser futuro (REST + chat); índice `(patient, -measured_at)` | 🟢 |

## Entidade: `SleepLog` (`health_logs.SleepLog`)

**Tabela:** `health_logs_sleeplog`
**Append-only**

| Campo | Tipo | Obrigatório | Restrições | Confiança |
|---|---|---|---|---|
| `id` | BigAutoField | Sim | PK | 🟢 |
| `patient` | FK → `patients.Patient` | Sim | `on_delete=CASCADE`, `related_name="sleep_logs"` | 🟢 |
| `duration_hours` | DecimalField(4,2) | Sim | validação via chat: `0 < h ≤ 24` | 🟢 |
| `quality_score` | PositiveSmallIntegerField | Sim | validação: `1–10`; default via chat `5` | 🟢 |
| `started_at` | DateTimeField | Sim | não pode ser futuro **apenas via chat** (REST não valida); índice `(patient, -started_at)` | 🟡 [Revisão Codex] |

## Entidade: `ActivityLog` (`health_logs.ActivityLog`)

**Tabela:** `health_logs_activitylog`
**Append-only**

| Campo | Tipo | Obrigatório | Restrições | Confiança |
|---|---|---|---|---|
| `id` | BigAutoField | Sim | PK | 🟢 |
| `patient` | FK → `patients.Patient` | Sim | `on_delete=CASCADE`, `related_name="activity_logs"` | 🟢 |
| `type` | CharField(40) | Sim | obrigatório, truncado a 40 via chat | 🟢 |
| `duration_min` | PositiveSmallIntegerField | Sim | validação: `≥ 1` | 🟢 |
| `performed_at` | DateTimeField | Sim | não pode ser futuro **apenas via chat** (REST não valida); índice `(patient, -performed_at)` | 🟡 [Revisão Codex] |

## Entidade: `NutritionNote` (`health_logs.NutritionNote`)

**Tabela:** `health_logs_nutritionnote`
**Append-only**

| Campo | Tipo | Obrigatório | Restrições | Confiança |
|---|---|---|---|---|
| `id` | BigAutoField | Sim | PK | 🟢 |
| `patient` | FK → `patients.Patient` | Sim | `on_delete=CASCADE`, `related_name="nutrition_notes"` | 🟢 |
| `note` | TextField | Sim | min `10` e max `1000` chars via chat; REST só max `1000` | 🟢 |
| `logged_at` | DateTimeField | Sim | não pode ser futuro **apenas via chat** (REST não valida); índice `(patient, -logged_at)` | 🟡 [Revisão Codex] |

### Resumo agregado (saída de `summarize`)

| Campo de saída | Fonte | Confiança |
|---|---|---|
| `avg_sleep_hours` | `Avg(duration_hours)` na janela | 🟢 |
| `avg_sleep_quality` | `Avg(quality_score)` na janela | 🟢 |
| `latest_weight_kg` | Último `value_kg` por `-measured_at` (sem janela) | 🟢 |
| `weight_trend_kg` | `latest − first(na janela)` | 🟢 |
| `total_activity_min` | `Sum(duration_min)` na janela (0 se vazio) | 🟢 |
| `last_nutrition_notes` | Top-3 por `-logged_at` (sem janela) | 🟢 |

---

## Entidade: `Conversation` (`conversations.Conversation`)

**Tabela:** `conversations_conversation`
**Soft-delete:** linha "removida" via `deleted_at` (manager `objects` exclui, `all_objects` inclui)
**Ordenação:** `-updated_at`

| Campo | Tipo | Obrigatório | Default | Restrições | Descrição | Confiança |
|---|---|---|---|---|---|---|
| `id` | BigAutoField | Sim | auto | PK | | 🟢 |
| `doctor` | FK → `accounts.User` | Sim | — | `on_delete=CASCADE`, `related_name="conversations"` | Médico dono da conversa | 🟢 |
| `patient` | FK → `patients.Patient` | Não | `null` | `on_delete=SET_NULL`, `related_name="conversations"` | Paciente vinculado (vazio até captura no chat) | 🟢 |
| `title` | CharField(200) | Não | `""` | — | Título; auto-definido para `prompt[:80]` na primeira mensagem; `"Nova conversa"` na criação | 🟢 |
| `created_at` | DateTimeField | Sim | `auto_now_add` | — | Criação | 🟢 |
| `updated_at` | DateTimeField | Sim | `auto_now` | — | Última atividade (título da listagem) | 🟢 |
| `deleted_at` | DateTimeField | Não | `null` | — | Soft delete (fill no DELETE) | 🟢 |

### Constraints e índices

| Tipo | Definição | Confiança |
|---|---|---|
| Index | `(doctor, -updated_at)` | 🟢 |
| Index | `(patient, -updated_at)` | 🟢 |

### Relacionamentos emitidos

| Campo | Alvo | on_delete | related_name | Confiança |
|---|---|---|---|---|
| `messages` (reverse de `Message.conversation`) | `conversations.Message` | CASCADE | `messages` | 🟢 |

> Soft delete **não** remove mensagens: conversa com `deleted_at` setado mantém `Message` em cascata até purga manual (não implementada — ver lacuna de retenção em `code-analysis.md`). 🟢

---

## Entidade: `Message` (`conversations.Message`)

**Tabela:** `conversations_message`
**Ordenação:** `created_at` (asc)

| Campo | Tipo | Obrigatório | Default | Restrições | Descrição | Confiança |
|---|---|---|---|---|---|---|
| `id` | BigAutoField | Sim | auto | PK | | 🟢 |
| `conversation` | FK → `conversations.Conversation` | Sim | — | `on_delete=CASCADE`, `related_name="messages"` | Conversa à qual pertence | 🟢 |
| `role` | CharField(10) | Sim | — | `choices=[USER, ASSISTANT, SYSTEM]` | Papel da mensagem no turno | 🟢 |
| `content` | TextField | Sim | — | — | Conteúdo (na prática: prompt do usuário ou resposta completa da IA) | 🟢 |
| `tokens_used` | PositiveIntegerField | Não | `null` | — | Tokens consumidos na resposta (ASSISTANT); `0` na boas-vindas | 🟢 |
| `blocked_by_guardrail` | BooleanField | Sim | `False` | — | True quando a resposta foi bloqueada por guardrail | 🟢 |
| `metadata` | JSONField | Não | `{}` | `default=dict, blank=True` | `citations`, `onboarding_mode`, `missing_basics`, `data_capture`; `welcome: true` na boas-vindas | 🟢 |
| `created_at` | DateTimeField | Sim | `auto_now_add` | — | Criação (ordena o histórico) | 🟢 |

### Constraints e índices

| Tipo | Definição | Confiança |
|---|---|---|
| Index | `(conversation, created_at)` | 🟢 |

### Enums / constantes

| Nome | Valores | Local | Confiança |
|---|---|---|---|
| `Message.ROLE_CHOICES` | `USER`, `ASSISTANT`, `SYSTEM` | models.py:42 | 🟢 |
| `WELCOME_CONVERSATION_TITLE` | `"Bem-vindo"` | services/welcome.py:7 | 🟢 |
| `WELCOME_METADATA_FLAG` | `"welcome"` | services/welcome.py:8 | 🟢 |
| `MAX_MESSAGES` (views) | `50` hardcoded | views.py:22 | 🟢 |
| `MAX_MESSAGES_PER_CONVERSATION` (service) | `50` via env (padrão) | services/chat.py:7 | 🟢 |

### Estrutura do metadata de resposta

| Chave | Origem | Confiança |
|---|---|---|
| `citations` | `[{source, chunk_id}]` — eventos de citação do RAG | 🟢 |
| `onboarding_mode` | presentes quando a resposta é de onboarding | 🟢 |
| `missing_basics` | lista de campos básicos faltantes do paciente | 🟢 |
| `data_capture` | metadados do que foi extraído do paciente | 🟢 |
| `welcome` | `true` apenas na mensagem de boas-vindas | 🟢 |

---

## Estruturas em memória — `ai_engine` (sem entidades ORM)

> O módulo `ai_engine` **não define modelos** no banco. Abaixo, as estruturas de dados em memória (Pydantic v2, dataclasses e typing) usadas no pipeline de IA. São a interface interna entre orquestrador, captura, providers e skills.

### `GenerateResult` (dataclass — orchestrator.py:31)

Saída de `generate()`. Campo `data_capture` espelha `CaptureResult.to_metadata()`; `missing_basics` pode vir do `still_missing` do capture.

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `content` | `str` | Resposta final (com `DISCLAIMER` anexado se não presente) | 🟢 |
| `tokens_used` | `int` | Tokens consumidos (0 se bloqueado por guardrail) | 🟢 |
| `blocked_by_guardrail` | `bool` | True quando guardrail de entrada ou saída bloqueou | 🟢 |
| `citations` | `list[dict]` | `[{source, chunk_id}]` do RAG | 🟢 |
| `onboarding_mode` | `str \| None` | `"focus"` \| `"soft"` quando em onboarding | 🟢 |
| `missing_basics` | `dict \| None` | Campos básicos faltantes do paciente | 🟢 |
| `data_capture` | `dict \| None` | Metadados da captura (saved/errors/still_missing) | 🟢 |

### `GuardrailResult` (dataclass — guardrails.py:6)

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `allowed` | `bool` | True se a mensagem/resposta passa | 🟢 |
| `reason` | `str` | `urgency` \| `diagnosis` \| `prescription` \| `gibberish` \| `forbidden_output` | 🟢 |
| `canned_reply` | `str` | Resposta canônica de bloqueio | 🟢 |

### `UserReadiness` (dataclass — skills/user_readiness.py:15)

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `is_complete` | `bool` | nome + `REQUIRED_PROFILE_FIELDS` + ≥1 WeightLog | 🟢 |
| `missing_name` | `bool` | Paciente sem `first_name` | 🟢 |
| `missing_profile_fields` | `list[str]` | Subconjunto de `(birth_date, biological_sex, height_cm)` | 🟢 |
| `missing_weight_log` | `bool` | Sem nenhum `WeightLog` | 🟢 |

Métodos: `missing_labels_pt()` (rótulos pt-BR para exibir no prompt) e `to_metadata()` (`{name, profile[], weight_log}`).

### `CaptureResult` (Pydantic — services/capture_models.py:55)

Resultado da captura automática. `saved` usa chaves: `name`, `profile`, `weight_log`, `sleep_log`, `activity_log`, `nutrition_note`.

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `saved` | `dict` | Entidades persistidas nesta mensagem | 🟢 |
| `errors` | `list[dict]` | Erros de validação por entidade `{entity, detail}` | 🟢 |
| `still_missing` | `dict` | `to_metadata()` de `UserReadiness` pós-persistência | 🟢 |
| `patient_id` | `int \| None` | Paciente vinculado à conversa (se houver) | 🟢 |
| `patient_created` | `bool` | Sempre `False` no MVP — atributo interno `_patient_just_created` nunca é definido (🟡) | 🟡 |

Métodos: `to_metadata()` (JSON-safe, converte date/datetime→ISO) e `saved_summary_pt()` (resumo legível em pt-BR do que foi salvo).

### `ExtractedUserData` e sub-modelos (Pydantic — services/capture_models.py)

Estrutura extraída da mensagem do médico (por regex e/ou LLM). Todos os campos opcionais.

| Modelo | Campos | Confiança |
|---|---|---|
| `ExtractedProfile` | `birth_date: date`, `biological_sex: Literal["M","F","OTHER"]`, `height_cm: int` | 🟢 |
| `ExtractedWeight` | `value_kg: float`, `measured_at: datetime` | 🟢 |
| `ExtractedSleep` | `duration_hours: float`, `quality_score: int`, `started_at: datetime` | 🟢 |
| `ExtractedActivity` | `type: str`, `duration_min: int`, `performed_at: datetime` | 🟢 |
| `ExtractedNutrition` | `note: str`, `logged_at: datetime` | 🟢 |
| `ExtractedUserData` | `name: str`, `profile`, `weight`, `sleep`, `activity`, `nutrition` | 🟢 |

### Tipos de provider (typing — providers/base.py)

| Nome | Tipo | Descrição | Confiança |
|---|---|---|---|
| `ChatMessage` | `TypedDict` | `{role: Literal[system,user,assistant], content: str}` | 🟢 |
| `LLMProvider` | `Protocol` | Contrato `stream(messages, max_tokens) -> Iterator[str]` e `complete(messages, max_tokens) -> (str, int)`; `complete_json` de facto | 🟢 |

### Enums / constantes relevantes

| Nome | Valores | Local | Confiança |
|---|---|---|---|
| `URGENCY_PATTERNS` | dor forte no peito, falta de ar, desmaio, não consigo respirar | guardrails.py:28-33 | 🟢 |
| `DIAGNOSIS_PATTERNS` | "qual meu diagnóstico", "eu estou com câncer", "diagnostique o que tenho", "isso é câncer/tumor/infecção" | guardrails.py:14-19 | 🟢 |
| `PRESCRIPTION_PATTERNS` | "que remédio devo tomar", "prescreva", "me receite", "dosagem de/para" | guardrails.py:21-26 | 🟢 |
| `FORBIDDEN_OUTPUT_PATTERNS` | "você tem câncer", "o paciente tem câncer/infarto/AVC/diabetes tipo 2", "diagnóstico é/confirmado/definitivo", "tome N mg/ml/gotas", "paciente deve tomar N mg/ml/gotas" | guardrails.py:71-77 | 🟢 |
| `_SHORT_OK_WORDS` | `ok, oi, ola, olá, sim, nao, não, m, f, kg, cm, h, min` | guardrails.py:52-68 | 🟢 |
| `REQUIRED_PROFILE_FIELDS` | `(birth_date, biological_sex, height_cm)` | skills/user_readiness.py:5 | 🟢 |
| `PROFILE_FIELD_LABELS` | labels pt-BR para exibição | skills/user_readiness.py:7-11 | 🟢 |
| `_ACTIVITY_TYPE_MAP` | normaliza verbos→tipos de atividade (corrida, caminhada, musculação, natação, ciclismo, yoga, crossfit, treino, academia) | capture_rules.py:63-77 | 🟢 |
| `CONVERSIONS` | kg↔lb, cm↔in, ml↔fl_oz | skills/unit_convert.py:5-12 | 🟢 |

---

## Entidade: `KnowledgeDocument` (`rag.KnowledgeDocument`)

**Tabela:** `rag_knowledgedocument`
**Ordem:** `-created_at`
**Finalidade:** metadados dos documentos da base de conhecimento indexados no ChromaDB. Os chunks ficam no vector store; o documento no Postgres guarda status e contagem.

| Campo | Tipo | Obrigatório | Default | Restrições | Descrição | Confiança |
|---|---|---|---|---|---|---|
| `id` | BigAutoField | Sim | auto | PK | | 🟢 |
| `title` | CharField(200) | Sim | — | truncado a 200 na view (`title[:200]`) | Título do documento | 🟢 |
| `file_name` | CharField(255) | Sim | — | truncado a 255 na view (`f.name[:255]`) | Nome original do arquivo | 🟢 |
| `mime_type` | CharField(80) | Sim | — | ∈ `{application/pdf, text/markdown, text/plain}` | Tipo MIME validado no upload | 🟢 |
| `status` | CharField(12) | Sim | `"PROCESSING"` | `choices=[PROCESSING, INDEXED, ERROR]` | Ciclo de vida da indexação | 🟢 |
| `chunk_count` | PositiveIntegerField | Não | `null` | — | Nº de chunks indexados (fill pós-ingestão) | 🟢 |
| `error_message` | TextField | Sim | `""` | truncado a 1000 chars na ingestão | Mensagem de erro de indexação | 🟢 |
| `uploaded_by` | FK → `accounts.User` | Não | `null` | `on_delete=SET_NULL`, `related_name="knowledge_documents"` | Quem enviou (preservado se usuário deletado) | 🟢 |
| `created_at` | DateTimeField | Sim | `auto_now_add` | — | Criação (base das métricas diárias) | 🟢 |
| `updated_at` | DateTimeField | Sim | `auto_now` | — | Última atualização | 🟢 |

### Constraints e índices

| Tipo | Definição | Confiança |
|---|---|---|
| PK | `id` | 🟢 |
| Ordenação | `-created_at` (Meta.ordering) | 🟢 |

> Sem `UniqueConstraint` em `title`/`file_name` — documentos duplicados são permitidos (novo id). 🟢

### Dados no ChromaDB (fora do Postgres)

| Campo | Valor | Confiança |
|---|---|---|
| `documents` | chunks de texto (split 1000/200) | 🟢 |
| `embeddings` | vetores `OpenAIEmbeddings` (1536 dim) | 🟢 |
| `metadatas.document_id` | `str(document.id)` | 🟢 |
| `metadatas.title` | título do documento | 🟢 |
| `metadatas.chunk_index` | índice do chunk (int) | 🟢 |
| ids | `f"{doc.id}-{i}-{uuid4().hex[:8]}"` | 🟢 |

### Enums / constantes

| Nome | Valores | Local | Confiança |
|---|---|---|---|
| `KnowledgeDocument.STATUS_CHOICES` | `PROCESSING`, `INDEXED`, `ERROR` | models.py:6-10 | 🟢 |
| `ALLOWED_MIMETYPES` | `application/pdf`, `text/markdown`, `text/plain` | ingestion.py:16 | 🟢 |
| `MAX_BYTES` | `10 * 1024 * 1024` (10MB) | ingestion.py:17 | 🟢 |
| `COLLECTION_NAME` | `mediclaw_kb` | vector_store.py:11 | 🟢 |
| chunk_size / chunk_overlap | `1000` / `200` | ingestion.py:28 | 🟢 |

---

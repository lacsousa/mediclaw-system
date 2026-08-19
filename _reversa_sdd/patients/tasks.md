# Patients, Tarefas de Implementação

> Sequência executável para reimplementar a unit `patients` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Unit `accounts` implementada (FK `doctor` aponta para `AUTH_USER_MODEL`)
- [ ] Modelo `Conversation` com campos `patient` (FK `SET_NULL`), `title`, `deleted_at` (unit `conversations`)
- [ ] Modelo `WeightLog` (unit `health_logs`) para anotação de `latest_weight_kg`
- [ ] Schema PostgreSQL criado e migrations aplicadas

## Tarefas

- [ ] **T-01**, Modelo `Patient` com FK do médico e constraint parcial
  - Origem no legado: `apps/patients/models.py:8-38`
  - Critério de pronto: migration cria tabela com `doctor` FK (`CASCADE`, `related_name="patients"`), `first_name` obrigatório (120), `birth_date`/`biological_sex`/`height_cm` opcionais, constraint parcial `unique_patient_name_dob_per_doctor`, índices `(doctor, first_name)` e `(doctor, -created_at)`, ordering `-created_at`
  - Confiança: 🟢

- [ ] **T-02**, Serializer de listagem com anotações read-only
  - Origem no legado: `apps/patients/serializers.py:6-27`
  - Critério de pronto: `PatientListSerializer` expõe os campos do modelo + `conversation_count`, `last_seen_at`, `latest_weight_kg` read-only
  - Confiança: 🟢

- [ ] **T-03**, Serializer de detalhe com logs e conversas aninhados
  - Origem no legado: `apps/patients/serializers.py:30-81`
  - Critério de pronto: `PatientDetailSerializer` estende o de listagem com `weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes` e `conversations` via `get_conversations` (ordenadas por `-updated_at`); sub-serializers definidos
  - Confiança: 🟢

- [ ] **T-04**, Anotação do queryset (`_annotate_patients`)
  - Origem no legado: `apps/patients/views.py:16-33`
  - Critério de pronto: adiciona `conversation_count` (Count com filtro `deleted_at__isnull=True`), `last_seen_at` (Max de `updated_at` das conversas não-deletadas) e `latest_weight_kg` (Subquery do `WeightLog` mais recente)
  - Confiança: 🟢

- [ ] **T-05**, Listagem paginada manual
  - Origem no legado: `apps/patients/views.py:36-51`
  - Critério de pronto: GET `/api/v1/patients/?page=N` → `{results, count, next}`; `PAGE_SIZE=20`; `next` como query string ou `null`
  - Confiança: 🟢

- [ ] **T-06**, Detalhe/atualização/deleção escopado ao dono
  - Origem no legado: `apps/patients/views.py:54-75`
  - Critério de pronto: busca anotada filtrada por `doctor=request.user`; id fora do escopo → 404 `NOT_FOUND`; GET → detalhe; PATCH parcial → 200; DELETE → 204
  - Confiança: 🟢

- [ ] **T-07**, Rotas da unit
  - Origem no legado: `apps/patients/urls.py`; `config/urls.py:33`
  - Critério de pronto: `""` → `list_patients`, `<int:patient_id>/` → `patient_detail`, montado em `api/v1/patients/`
  - Confiança: 🟢

- [ ] **T-08**, Service `ensure_or_create_patient` (captura via chat)
  - Origem no legado: `apps/patients/services/patient.py:10-42`
  - Critério de pronto: conversa sem paciente → cria paciente tentativo e vincula em `conv.patient` + `conv.title`; conversa com paciente de nome vazio → preenche apenas o nome; loga `patient_created` em debug
  - Confiança: 🟢

- [ ] **T-09**, Service `resolve_patient_dob` (dedup por nome+DOB)
  - Origem no legado: `apps/patients/services/patient.py:45-94`
  - Critério de pronto: match `first_name__iexact` + `birth_date` por médico → re-vincula conversa ao existente e deleta tentativo sem dados (mantém tentativo com dados); sem match → grava DOB no tentativo; conversa sem paciente → `None`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Listagem: 3 pacientes → `results` com anotações, `count=3`, `next=null`
- [ ] **TT-02**, Paginação: 45 pacientes → página 3 com 5 itens, `count=45`, `next=null`
- [ ] **TT-03**, Detalhe: paciente com 2 pesos e 1 conversa → `weight_logs` e `conversations` populados
- [ ] **TT-04**, Escopo: paciente de outro médico → 404 `NOT_FOUND`
- [ ] **TT-05**, PATCH parcial: envia apenas `height_cm` → somente o campo muda
- [ ] **TT-06**, DELETE: 204; conversa permanece com `patient_id` nulo (`SET_NULL`)
- [ ] **TT-07**, `ensure_or_create_patient`: cria tentativo e seta `conv.title`; chamada repetida não duplica
- [ ] **TT-08**, `resolve_patient_dob`: match existente re-vincula e deleta tentativo sem dados; tentativo com dados é preservado; sem match grava DOB
- [ ] **TT-09**, Anotação: conversa soft-deletada (`deleted_at` preenchido) não conta em `conversation_count` nem `last_seen_at`

## Tarefas de Migração de Dados (se aplicável)

- n/a — reimplementação do schema a partir do zero. 🟡

## Ordem Sugerida

1. T-01 (modelo) + T-07 (rotas) primeiro: base da unit.
2. T-02 → T-03 (serializers) e T-04 → T-06 (views) — dependem do modelo.
3. T-08 → T-09 (services de captura) — dependem de `Conversation` e dos models de log (units `conversations` e `health_logs`).
4. Testes TT-01 a TT-06 (HTTP) após views; TT-07 a TT-09 (services) após models de log prontos.

## Lacunas Pendentes (🔴)

- [ ] Validar comportamento do log `patient_created` (gap do Arquiteto: observado "sempre False" — checar nível de log do `get_logger`).
- [ ] Decidir destino do paciente tentativo **com dados** quando o dedup encontra outro paciente (atualmente fica órfão).

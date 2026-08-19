# Patients — Requisitos

> Contrato operacional da unit `patients` (cadastro de pacientes e captura via chat).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Módulo de registro de pacientes por médico: CRUD escopado ao médico dono (`doctor`), com listagem paginada anotada por `conversation_count`, `last_seen_at` e `latest_weight_kg`, detalhe com logs biométricos, refeições e conversas. Inclui a criação e deduplicação de pacientes a partir de dados capturados no chat (`ensure_or_create_patient` / `resolve_patient_dob`), que mantêm um paciente tentativo por conversa e mesclam ao preencher a data de nascimento.

## Responsabilidades

- Listar pacientes do médico autenticado com paginação (20/página) e anotações derivadas
- Expor detalhe do paciente com histórico biométrico (peso, sono, atividade), refeições e conversas
- Atualizar parcialmente e deletar paciente (escopo do dono)
- Garantir unicidade de nome + data de nascimento por médico (quando DOB preenchida)
- Criar/recuperar o paciente vinculado a uma conversa a partir do nome capturado no chat
- Resolver a data de nascimento com dedup: reutilizar paciente existente e descartar o tentativo sem dados

## Regras de Negócio

- **RN-01** — Paciente pertence a um médico (`doctor` FK); acesso apenas pelo dono (querys filtradas por `doctor=request.user`). 🟢
- **RN-02** — Unicidade de `(doctor, first_name, birth_date)` quando `birth_date` presente (constraint parcial `unique_patient_name_dob_per_doctor`). 🟢
- **RN-03** — `first_name` é obrigatório (≤ 120); `birth_date`, `biological_sex` (M/F/OTHER) e `height_cm` são opcionais. 🟢
- **RN-04** — Contagem/última atividade consideram apenas conversas **não** soft-deletadas (`deleted_at__isnull=True`). 🟢
- **RN-05** — `ensure_or_create_patient`: cada conversa mantém um único paciente tentativo; se a conversa já tem paciente com `first_name` vazio, apenas preenche o nome. 🟢
- **RN-06** — `resolve_patient_dob`: ao capturar DOB, busca paciente existente com `first_name__iexact` + `birth_date` do mesmo médico; se encontrado, re-vincula a conversa e deleta o tentativo (apenas se este não tiver logs/refeições). 🟢
- **RN-07** — Paciente não encontrado no escopo do médico → `404 NOT_FOUND` (mesmo para id inexistente ou de outro médico, sem vazar existência). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Listar pacientes do médico com paginação e anotações | Must | GET `/api/v1/patients/?page=2` → 200 `{results, count, next}`; cada item com `conversation_count`, `last_seen_at`, `latest_weight_kg` |
| RF-02 | Consultar detalhe do paciente com histórico completo | Must | GET `/api/v1/patients/<id>/` → 200 com `weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes`, `conversations` (ordenadas por `-updated_at`) |
| RF-03 | Atualizar dados do paciente (parcial) | Must | PATCH `/api/v1/patients/<id>/` com subset de campos → 200; fields read-only (`id`, `created_at`, `updated_at`, anotações) ignoradas/ilegíveis |
| RF-04 | Deletar paciente | Must | DELETE `/api/v1/patients/<id>/` → 204; conversas mantêm FK `SET_NULL` |
| RF-05 | Paciente inexistente ou de outro médico → 404 | Must | GET/PATCH/DELETE em id fora do escopo → 404 `NOT_FOUND` (não 403) |
| RF-06 | Captura de paciente via chat: criar/recuperar por conversa | Must | `ensure_or_create_patient(conversation_id, doctor_id, first_name)` → paciente vinculado à conversa e `conv.title` = nome |
| RF-07 | Captura de DOB via chat com dedup | Should | `resolve_patient_dob(conversation_id, doctor_id, birth_date)` → reutiliza paciente existente (nome + DOB) e deleta tentativo sem dados |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | Acesso escopado ao dono: todas as querys filtram `doctor=request.user` | `apps/patients/views.py:41,58` | 🟢 |
| Segurança | Rotas exigem `IsAuthenticated` (JWT Bearer) | `apps/patients/views.py:36-37,54-55` | 🟢 |
| Desempenho | Listagem com anotação via subquery (evita N+1 em `latest_weight_kg`) | `apps/patients/views.py:18-33` | 🟢 |
| Desempenho | Índices compostos `(doctor, first_name)` e `(doctor, -created_at)` | `apps/patients/models.py:31-34` | 🟢 |
| Integridade | Constraint parcial de unicidade no banco (não só na aplicação) | `apps/patients/models.py:24-30` | 🟢 |
| Privacidade | Dados de saúde do paciente removidos em cascata ao deletar o médico (LGPD) | `apps/patients/models.py:9-13` (`on_delete=CASCADE` do doctor) | 🟢 |

## Critérios de Aceitação

```gherkin
# Listagem — happy path
Dado um médico autenticado com 3 pacientes (1 sem conversas)
Quando faço GET em /api/v1/patients/
Então recebo 200 com 3 itens, cada um com conversation_count, last_seen_at e latest_weight_kg
E a página indica next=null (3 < 20)

# Listagem — paginação
Dado um médico com 45 pacientes
Quando faço GET em /api/v1/patients/?page=3
Então recebo 5 itens, count=45 e next=null

# Detalhe — histórico
Dado um paciente com 2 logs de peso e 1 conversa
Quando faço GET em /api/v1/patients/<id>/
Então recebo 200 com weight_logs, sleep_logs, activity_logs, nutrition_notes e conversations

# Detalhe — fora do escopo
Dado um paciente de outro médico
Quando faço GET em /api/v1/patients/<id>/
Então recebo 404 NOT_FOUND

# Atualização parcial
Dado um paciente com height_cm nulo
Quando faço PATCH em /api/v1/patients/<id>/ enviando apenas {"height_cm": 178}
Então recebo 200 e somente height_cm é alterado

# Deleção
Dado um paciente com 1 conversa vinculada
Quando faço DELETE em /api/v1/patients/<id>/
Então recebo 204 e a conversa permanece com patient_id nulo (SET_NULL)
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| CRUD escopado ao dono (RF-01 a RF-05) | Must | Caminho crítico do registro de pacientes |
| Anotações de listagem (count, last_seen, peso) | Should | Enriquecimento da listagem, mas com fallback (dados podem ser consultados no detalhe) |
| Captura via chat (RF-06) | Must | Dependência do fluxo de onboarding do chat (ADRs 004/008) |
| Dedup por nome + DOB (RF-07) | Should | Evita duplicação, mas os dados capturados via chat também podem ser corrigidos manualmente |
| Índices e subquery de peso | Should | Otimização, não requisito funcional |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/patients/models.py` | `Patient`, constraint parcial, índices | 🟢 |
| `apps/patients/views.py` | `_annotate_patients`, `list_patients`, `patient_detail` | 🟢 |
| `apps/patients/serializers.py` | `PatientListSerializer`, `PatientDetailSerializer`, sub-serializers de logs | 🟢 |
| `apps/patients/urls.py` | rotas `/api/v1/patients/` e `/api/v1/patients/<id>/` | 🟢 |
| `apps/patients/services/patient.py` | `ensure_or_create_patient`, `resolve_patient_dob` | 🟢 |
| `apps/conversations/models.py` | `Conversation.patient` (`SET_NULL`, `related_name="conversations"`), `deleted_at` | 🟢 |

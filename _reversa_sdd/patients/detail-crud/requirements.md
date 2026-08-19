# Patients / Detail & CRUD — Requisitos

> Contrato operacional do caso de uso **Detalhe, edição e exclusão de paciente** (`GET/PATCH/DELETE /api/v1/patients/<id>/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Consulta o histórico completo do paciente (logs biométricos, refeições e conversas), atualiza dados de forma parcial e deleta o paciente. O acesso é escopado ao médico dono: id de outro médico ou inexistente → `404 NOT_FOUND` (sem vazar existência).

## Regras de Negócio

- **RN-01** — Paciente buscado com `doctor=request.user`; fora do escopo ou inexistente → 404 (não 403). 🟢
- **RN-02** — PATCH é parcial; campos derivados (`id`, `created_at`, `updated_at`, anotações) são read-only. 🟢
- **RN-03** — DELETE remove o paciente; conversas mantêm FK `SET_NULL` (não são deletadas). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Consultar detalhe com histórico completo | Must | GET `/api/v1/patients/<id>/` → 200 com `weight_logs`, `sleep_logs`, `activity_logs`, `nutrition_notes`, `conversations` |
| RF-02 | Atualizar dados parcialmente | Must | PATCH `{"height_cm": 178}` → 200, apenas `height_cm` alterado |
| RF-03 | Deletar paciente mantendo conversas | Must | DELETE `/api/v1/patients/<id>/` → 204; conversas permanecem com `patient_id` nulo |
| RF-04 | 404 para fora do escopo | Must | GET/PATCH/DELETE em id inexistente ou de outro médico → 404 `NOT_FOUND` |

## Critérios de Aceitação

```gherkin
Dado um paciente com 2 logs de peso e 1 conversa
Quando faço GET em /api/v1/patients/<id>/
Então recebo 200 com weight_logs, sleep_logs, activity_logs, nutrition_notes e conversations

Dado um paciente de outro médico ou id inexistente
Quando faço GET/PATCH/DELETE em /api/v1/patients/<id>/
Então recebo 404 NOT_FOUND

Dado um paciente com height_cm nulo
Quando faço PATCH em /api/v1/patients/<id>/ enviando apenas {"height_cm": 178}
Então recebo 200 e somente height_cm é alterado

Dado um paciente com 1 conversa vinculada
Quando faço DELETE em /api/v1/patients/<id>/
Então recebo 204 e a conversa permanece com patient_id nulo
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/patients/views.py:50-110` | `patient_detail` | 🟢 |
| `apps/patients/serializers.py` | `PatientDetailSerializer`, `PatientListSerializer`, sub-serializers | 🟢 |
| `apps/patients/models.py` | `Patient`, `Conversation.patient SET_NULL` | 🟢 |

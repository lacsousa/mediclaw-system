# Accounts / Me — Requisitos

> Contrato operacional do caso de uso **Perfil próprio** (`GET/PATCH/DELETE /api/v1/auth/me/`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Consulta, atualiza e deleta o perfil do usuário autenticado. PATCH atualiza apenas os campos enviados (nome e/ou e-mail, com validação de unicidade exceto o próprio usuário). DELETE remove a conta com todos os dados sensíveis dependentes em cascata (LGPD Art. 11).

## Regras de Negócio

- **RN-01** — Requer autenticação JWT Bearer (rota `IsAuthenticated`). 🟢
- **RN-02** — PATCH é parcial (`partial=True`): atualiza apenas `name` e/ou `email` enviados, via `update_fields`. 🟢
- **RN-03** — Mudança de e-mail valida unicidade (`email__iexact`) excluindo o próprio `pk`. 🟢
- **RN-04** — DELETE remove o usuário e dependentes em cascata (`on_delete=CASCADE` em patients, conversas, logs). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Consultar perfil próprio autenticado | Must | GET `/api/v1/auth/me/` → 200 `UserSerializer` |
| RF-02 | Atualizar nome e/ou e-mail de forma parcial | Must | PATCH `/api/v1/auth/me/` `{name}` → 200 com apenas `first_name` alterado |
| RF-03 | Rejeitar e-mail duplicado (exceto próprio) | Must | PATCH com e-mail de outro usuário → 400 `VALIDATION_ERROR` |
| RF-04 | Deletar a própria conta com remoção em cascata | Must | DELETE `/api/v1/auth/me/` → 204; dados sensíveis dependentes removidos |

## Critérios de Aceitação

```gherkin
Dado um usuário autenticado
Quando faço GET em /api/v1/auth/me/
Então recebo 200 com id, email, first_name, role, accepted_terms_at

Dado um usuário autenticado
Quando faço PATCH em /api/v1/auth/me/ enviando apenas name
Então recebo 200 e somente o campo first_name é alterado

Dado um usuário autenticado com conversas e logs biométricos
Quando faço DELETE em /api/v1/auth/me/
Então recebo 204 e todos os dados dependentes são removidos em cascata

Dado um usuário autenticado tentando usar e-mail de outro usuário
Quando faço PATCH em /api/v1/auth/me/
Então recebo 400 VALIDATION_ERROR indicando e-mail já em uso
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/accounts/views.py:66-93` | `me` | 🟢 |
| `apps/accounts/serializers.py:54-61` | `MeUpdateSerializer` | 🟢 |
| `apps/accounts/models.py` | `User` | 🟢 |
| `apps/patients/models.py:11` | `Patient.doctor` CASCADE | 🟢 |
| `apps/conversations/models.py:15` | `Conversation.doctor` CASCADE | 🟢 |

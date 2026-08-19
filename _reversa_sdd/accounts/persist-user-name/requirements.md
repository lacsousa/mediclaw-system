# Accounts / persist_user_name — Requisitos

> Contrato operacional do caso de uso **Captura de nome via chat** (`apps/accounts/services/persist.py`).
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Service chamado pelo orquestrador de IA durante a captura de dados no chat para gravar o nome do usuário (`first_name`). Não expõe endpoint HTTP; valida o nome e persiste com `update_fields`.

## Regras de Negócio

- **RN-01** — Nome é aplicado `strip()` antes da validação. 🟢
- **RN-02** — Tamanho válido: `2 ≤ len ≤ 120`; fora disso → `ValidationError` do DRF. 🟢
- **RN-03** — Usuário buscado por `pk`; se inexistente, propaga erro do ORM (`User.DoesNotExist` → 404 via handler). 🟡
- **RN-04** — Gravação usa `update_fields=["first_name"]`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Persistir nome do usuário a partir de service | Must | `persist_user_name(user_id, "João")` → `{"first_name": "João"}` gravado |
| RF-02 | Validar tamanho do nome | Must | Nome com < 2 chars ou > 120 → `ValidationError` |
| RF-03 | Retornar nome limpo | Must | Retorno com `first_name` após `strip` |

## Critérios de Aceitação

```gherkin
Dado um user_id existente e nome "  João  "
Quando chamo persist_user_name(user_id, nome)
Então retorna {"first_name": "João"} e o first_name do usuário é gravado

Dado um nome com 1 caractere
Quando chamo persist_user_name(user_id, nome)
Então é lançado ValidationError
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/accounts/services/persist.py:9-18` | `persist_user_name` | 🟢 |
| `apps/ai_engine/` | chamada durante captura de dados | 🟡 |

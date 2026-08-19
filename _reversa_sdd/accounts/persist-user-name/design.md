# Accounts / persist_user_name, Design Técnico

> Contrato operacional de **COMO** a captura de nome é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `persist_user_name` | `(user_id: int, name: str) -> dict` | `{"first_name": str}` | Sem request HTTP; usado na captura via chat |

## Fluxo Principal

1. `cleaned = (name or "").strip()`. (`apps/accounts/services/persist.py:9`) 🟢
2. Valida `2 ≤ len(cleaned) ≤ 120`; falha lança `ValidationError`. (`persist.py:10-13`) 🟢
3. `user = User.objects.get(pk=user_id)`; se inexistente, `User.DoesNotExist` se propaga. (`persist.py:15`) 🟡
4. `user.first_name = cleaned`; `user.save(update_fields=["first_name"])`. (`persist.py:16-17`) 🟢
5. Retorna `{"first_name": cleaned}`. (`persist.py:18`) 🟢

## Fluxos Alternativos

- **[Nome inválido]:** `ValidationError` do DRF — a captura no chat trata como dado não persistível. (`persist.py:10-13`) 🟢
- **[Usuário inexistente]:** `User.DoesNotExist` propaga para o handler DRF → 404. 🟡

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.accounts.models.User` | Alvo da gravação | `User.objects.get(pk=user_id)` |
| `rest_framework` | Erro de validação | `ValidationError` |
| `apps.ai_engine` | Caller (captura de dados no chat) | Orquestrador chama o service |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Service layer sem HTTP (chamável por IA) | `persist.py:9` | 🟢 |
| `update_fields` para escrita mínima | `persist.py:17` | 🟢 |
| Validação de tamanho no service (não no model) | `persist.py:10-13` | 🟢 |

## Riscos e Lacunas

- 🟡 Erro de usuário inexistente não é mapeado explicitamente para `NOT_FOUND` — depende do handler global.
- 🟢 Nome é dado pessoal, mas apenas metadados são logados (sem conteúdo no log).

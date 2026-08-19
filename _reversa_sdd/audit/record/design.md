# Audit / Record, Design Técnico

> Contrato operacional de **COMO** a auditoria é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

| Símbolo | Assinatura | Retorno |
|---------|-----------|---------|
| `record` | `(event: str, *, user=None, **kwargs) -> None` | `None` (`apps/audit/services/log.py:1-4`) |

> ⚠️ **Stub `pass`:** assinatura documenta o contrato; o corpo não executa nada. Nenhum modelo `ActivityLog` existe no código.

## Fluxo Principal

1. `record(event, *, user=None, **kwargs)` recebe o nome do evento e metadados. 🟢
2. Corpo `pass` — **nenhuma ação executada**. 🟢
3. Chamadores conhecidos: `ai_engine` (`GUARDRAIL_BLOCKED`, `MESSAGE_SENT` em `orchestrator.py:200,226,245`), `rag` (`KB_UPLOAD`, `KB_DELETE` em `views.py:46-50,130-131`), `accounts` (`ADMIN_CREATED_USER` em `views.py:63`). 🟢

### Roteamento admin (`apps/audit/urls.py:6-9`)

1. `path("users/", admin_create_user)` — delega a `apps.accounts.views`; valida com `AdminCreateUserSerializer`, chama `record("ADMIN_CREATED_USER", user=request.user)`, retorna 201 `UserSerializer`. 🟢
2. `path("metrics/", metrics)` — delega a `apps.rag.views`; `metrics` agrega métricas diárias e exige `IsAdminRole`. 🟢

## Fluxos Alternativos

- **[Evento de qualquer unidade]:** `record(...)` chamado e sem efeito (stub) — sem erro, sem registro. 🟢
- **[`/api/v1/admin/knowledge/metrics/`]:** 404 — a rota `metrics` vive no urlconf `audit`, não no `rag`. 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.accounts.views.admin_create_user` | Endpoint admin de criação de usuário | montado em `urls.py:3,7` |
| `apps.rag.views.metrics` | Métricas operacionais | montado em `urls.py:4,8` |

## Decisões de Design Identificadas

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| Auditoria adiada: contrato `record` como stub (ADR 007) | `apps/audit/services/log.py:1-4` | 🟢 |
| App `audit` como roteador admin (sem views próprias) | `apps/audit/urls.py:1-9`; `config/urls.py:36` | 🟢 |
| Nenhum modelo `ActivityLog` implementado | ausência de `models.py`/migrations | 🟢 |

## Riscos e Lacunas

- 🔴 **Auditoria inexistente em produção:** eventos nunca persistidos — sem trilha LGPD/compliance no MVP.
- 🟡 Acoplamento de roteamento: o contrato de `metrics` pertence ao `rag`, mas a rota vive no `audit`.
- 🟡 Assinatura de `record` subdeterminada — contrato de metadados só fixado quando `ActivityLog` for implementado.

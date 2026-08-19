# Audit, Design Técnico

> Contrato operacional de **COMO** a unit `audit` é construída, extraído do código legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

A unit **não possui endpoints HTTP próprios nem views** — seu urlconf `apps/audit/urls.py` importa views de outras units e as monta sob `/api/v1/admin/` (`config/urls.py:36`). 🟢

### Funções / classes públicas

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `record` | `(event: str, *, user=None, **kwargs) -> None` | `None` | **Stub `pass`** — assinatura documenta o contrato, mas nada é registrado no MVP (`log.py:1-4`) |

### Rotas montadas (urlconf, não views da unit)

| Rota | View (origem) | Propósito |
|------|---------------|-----------|
| `/api/v1/admin/users/` | `apps.accounts.views.admin_create_user` | Criação de usuário (admin) via `AdminCreateUserSerializer` |
| `/api/v1/admin/metrics/` | `apps.rag.views.metrics` | Métricas agregadas (role `ADMIN`) |

## Fluxo Principal

### 1. Auditoria via `record` (`apps/audit/services/log.py:1-4`)

1. `record(event, *, user=None, **kwargs)` recebe o nome do evento e metadados. 🟢
2. O corpo é `pass` — **nenhuma ação é executada** no MVP. 🟢
3. Chamadores conhecidos hoje: `ai_engine` (`GUARDRAIL_BLOCKED`, `MESSAGE_SENT` em `orchestrator.py:200,226,245`), `rag` (`KB_UPLOAD`, `KB_DELETE` em `views.py:46-50,130-131`), `accounts` (`ADMIN_CREATED_USER` em `views.py:63`). 🟢

### 2. Roteamento admin (`apps/audit/urls.py:6-9`)

1. `path("users/", admin_create_user)` — delega a `apps.accounts.views`; `admin_create_user` valida com `AdminCreateUserSerializer`, chama `record("ADMIN_CREATED_USER", user=request.user)` e retorna `UserSerializer(user).data` 201. 🟢
2. `path("metrics/", metrics)` — delega a `apps.rag.views`; `metrics` agrega métricas diárias e exige `IsAdminRole`. 🟢

## Fluxos Alternativos

- **[Evento de auditoria em qualquer unidade]:** `record(...)` é chamado e não produz efeito (stub) — sem erro, sem registro. 🟢
- **[Requisição a `/api/v1/admin/knowledge/metrics/`]:** 404 — nenhuma rota do urlconf `rag` casa com o path (a rota `metrics` vive no urlconf `audit`). 🟢

## Dependências

| Componente | Motivo | Como usa |
|------------|--------|----------|
| `apps.accounts.views.admin_create_user` | Endpoint admin de criação de usuário | Importado e montado em `urls.py:3,7` |
| `apps.rag.views.metrics` | Métricas operacionais | Importado e montado em `urls.py:4,8` |
| `apps.accounts.serializers` (`AdminCreateUserSerializer`, `UserSerializer`) | Validação/serialização da rota users | Via `admin_create_user` (dependência transitiva) |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Auditoria **adiada**: contrato `record` como stub `pass` (ADR 007 "auditoria adiada") | `apps/audit/services/log.py:1-4` | 🟢 |
| App `audit` funciona como **roteador admin** — sem views próprias, importa de `accounts` e `rag` | `apps/audit/urls.py:1-9`; `config/urls.py:36` | 🟢 |
| Nenhum modelo `ActivityLog` implementado (estrutura de projeto cita, código não tem) | ausência de `models.py`/migrations no app | 🟢 |

## Estado Interno

- **Sem estado persistente.** A unit não possui modelos, tabelas, caches ou singletons. Toda a lógica é importação de views de outras units + stub de auditoria. 🟢
- `record` não mantém buffer/lista de eventos — chamadas são descartadas. 🟢

## Observabilidade

- **Sem logs, métricas ou traces** emitidos pela unit (o corpo de `record` é vazio; o urlconf não registra observabilidade). 🟢
- A única "observabilidade" do MVP é o endpoint `metrics` delegado à unit `rag` (agrega `Message.tokens_used`, `blocked_by_guardrail`, contagens de usuários/conversas/documentos). 🟢

## Riscos e Lacunas

- 🔴 **Auditoria inexistente em produção:** `record` é stub — eventos `GUARDRAIL_BLOCKED`, `MESSAGE_SENT`, `KB_UPLOAD`, `KB_DELETE`, `ADMIN_CREATED_USER` nunca são persistidos. Sem trilha de auditoria (LGPD/compliance) no MVP. ADR 007 registra a decisão de adiar.
- 🟡 **Acoplamento de roteamento:** `audit/urls.py` depende de views de duas outras units; o contrato do endpoint `metrics` pertence à unit `rag`, mas a rota vive na unit `audit` — dificulta rastreabilidade e futura movimentação de rotas.
- 🟡 **Assinatura de `record` subdeterminada:** sem implementação, não há contrato definitivo de metadados (`metadata` vs kwargs posicionais, schema de eventos) — o contrato só será fixado quando o modelo `ActivityLog` for implementado.

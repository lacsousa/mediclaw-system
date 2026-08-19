# Audit — Requisitos

> Contrato operacional da unit `audit` (auditoria + roteador admin).
> Foco no **QUE** o módulo faz. O **COMO** está em `design.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

A unit `audit` é mínima no MVP: define o contrato de auditoria `record(event, *, user=None, **kwargs)` — **implementado como stub `pass`** (ADR 007 "auditoria adiada") — e funciona como **roteador admin**, montando em `/api/v1/admin/` dois endpoints de outras units: criação de usuário (`accounts.views.admin_create_user`) e métricas operacionais (`rag.views.metrics`). Não possui modelos, migrations ou lógica de negócio próprios.

## Responsabilidades

- Expor o contrato de registro de eventos de auditoria `record`, consumido por `ai_engine` (`GUARDRAIL_BLOCKED`, `MESSAGE_SENT`) e `rag` (`KB_UPLOAD`, `KB_DELETE`) — **stub no MVP, nada persiste**
- Montar as rotas admin em `/api/v1/admin/`: `users/` (criação de usuário via `accounts`) e `metrics/` (métricas via `rag`)

## Regras de Negócio

- **RN-01** — `record` aceita `event: str`, `user` (opcional, keyword-only) e `**kwargs` (ex.: `metadata`); **no MVP não executa nenhuma ação** (corpo `pass`). 🟢
- **RN-02** — Nenhum modelo `ActivityLog` existe no código; a doc de projeto cita `ActivityLog` na estrutura, mas não há migrations nem tabela. 🟢
- **RN-03** — O urlconf `audit/urls.py` importa views de **outras units** (`accounts`, `rag`) — o app `audit` é o ponto de montagem das rotas admin. 🟢
- **RN-04** — O caminho real de métricas é `/api/v1/admin/metrics/` (via `audit/urls.py:9`), **não** `/api/v1/admin/knowledge/metrics/` como documentado no contrato da unit `rag`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Contrato `record` para auditoria de eventos | Must | `record("MESSAGE_SENT", user=u, metadata={...})` não levanta erro; no MVP é no-op (stub) |
| RF-02 | Montagem de `/api/v1/admin/users/` | Must | `POST /api/v1/admin/users/` chega em `accounts.views.admin_create_user` (criação de usuário admin) |
| RF-03 | Montagem de `/api/v1/admin/metrics/` | Must | `GET /api/v1/admin/metrics/` chega em `rag.views.metrics` (role `ADMIN`) |
| RF-04 | Persistência de eventos de auditoria | Won't (MVP) | Nenhuma tabela/registro é gravado por `record` no MVP — comportamento a implementar em épico futuro (ver ADR 007) |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | Rotas admin sob `/api/v1/admin/`; `metrics` exige `IsAdminRole`, `users` expõe criação de usuário | `audit/urls.py:6-9`; `rag/views.py:89`; `accounts/views.py` | 🟢 |
| Privacidade | Contrato `record` não define metadados mínimos; nada logado no MVP (não há logging de PII porque não há implementação) | `audit/services/log.py:1-4` | 🟢 |
| Disponibilidade | `record` é chamado em caminhos críticos (`generate`, upload) mas é no-op — zero risco de falha em runtime no MVP | `apps/ai_engine/orchestrator.py:200,226,245`; `apps/rag/views.py:46-50,130-131` | 🟢 |

## Critérios de Aceitação

```gherkin
# record — contrato (stub)
Dado o contrato record(event, *, user=None, **kwargs)
Quando chamo record("MESSAGE_SENT", user=user, metadata={"tokens_used": 10})
Então a chamada não levanta exceção e não persiste nenhum registro (MVP)

# metrics — roteamento admin
Dado um usuário autenticado com role "ADMIN"
Quando chamo GET /api/v1/admin/metrics/
Então recebo 200 com os agregados de mensagens/tokens/guardrails/documentos

# metrics — roteamento admin sem role
Dado um usuário autenticado com role != "ADMIN"
Quando chamo GET /api/v1/admin/metrics/
Então recebo 403 FORBIDDEN

# users — roteamento admin
Quando chamo POST /api/v1/admin/users/
Então a rota é resolvida por accounts.views.admin_create_user
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Contrato `record` (RF-01) | Must | Chamado em caminhos críticos (chat, RAG) mesmo sendo stub |
| Roteamento admin (RF-02, RF-03) | Must | Expõe as únicas funcionalidades admin reais do MVP |
| Persistência de auditoria (RF-04) | Won't | Adiada (ADR 007); nada a reimplementar no MVP |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `apps/audit/services/log.py:1-4` | `record` (stub `pass`) | 🟢 |
| `apps/audit/urls.py:1-9` | urlpatterns (`users/`, `metrics/`) | 🟢 |
| `config/urls.py:36` | montagem `api/v1/admin/` → `apps.audit.urls` | 🟢 |
| `apps/accounts/views.py` | `admin_create_user` (consumido via rota) | 🟢 |
| `apps/rag/views.py:88-114` | `metrics` (consumido via rota) | 🟢 |

# Audit, Tarefas de Implementação

> Sequência executável para reimplementar a unit `audit` a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Unit `accounts` implementada — `admin_create_user` em `apps/accounts/views.py`, `AdminCreateUserSerializer`, `UserSerializer`
- [ ] Unit `rag` implementada — `metrics` em `apps/rag/views.py` (role `ADMIN`)
- [ ] Dependências: nenhuma além das units acima (a unit `audit` não adiciona pacotes)
- [ ] Variáveis de ambiente: nenhuma específica da unit

## Tarefas

- [ ] **T-01**, Contrato de auditoria `record` (stub)
  - Origem no legado: `apps/audit/services/log.py:1-4`
  - Critério de pronto: `def record(event: str, *, user=None, **kwargs) -> None` com corpo `pass`; docstring indica expansão futura ("Será expandido no Epic 3"); chamadas como `record("MESSAGE_SENT", user=request.user, metadata={...})` não levantam erro
  - Confiança: 🟢

- [ ] **T-02**, urlconf de rotas admin (`users/`, `metrics/`)
  - Origem no legado: `apps/audit/urls.py:1-9`; `config/urls.py:36`
  - Critério de pronto: `urlpatterns = [path("users/", admin_create_user), path("metrics/", metrics)]` importando `admin_create_user` de `apps.accounts.views` e `metrics` de `apps.rag.views`; montagem `path("api/v1/admin/", include("apps.audit.urls"))` no `config/urls.py`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, `record` é no-op: `record("MESSAGE_SENT", user=u, metadata={"tokens_used": 10})` executa sem erro e não persiste nada (verificar ausência de efeitos colaterais)
- [ ] **TT-02**, `record` aceita `event` posicional + `user` keyword-only + `**kwargs` (testar `record("EVENT", user=u)` e `record("EVENT", metadata={})`)
- [ ] **TT-03**, `/api/v1/admin/users/` resolve para `admin_create_user` (POST com payload válido → 201 com dados do usuário; ver contract da unit `accounts`)
- [ ] **TT-04**, `/api/v1/admin/metrics/` resolve para `metrics` (role `ADMIN` → 200; role não-admin → 403 — cobertura detalhada na unit `rag`)

## Tarefas de Migração de Dados (se aplicável)

- n/a — a unit não cria tabelas nem mantém estado; o stub `record` não persiste nada. 🟢

## Ordem Sugerida

1. T-01 (contrato `record`) — trivial, sem dependências; desbloqueia os chamadores (`ai_engine`, `rag`, `accounts`) que já esperam a assinatura.
2. T-02 (urlconf) — depende das units `accounts` (`admin_create_user`) e `rag` (`metrics`); a montagem em `config/urls.py` deve vir junto.
3. Testes TT-01/TT-02 (contrato) podem rodar isolados; TT-03/TT-04 dependem das units externas.
4. **Não implementar persistência de auditoria no MVP** — o contrato `record` deve permanecer stub até a decisão do ADR 007.

## Lacunas Pendentes (🔴)

- [ ] **Auditoria inexistente (ADR 007 "auditoria adiada"):** `record` é stub — `GUARDRAIL_BLOCKED`, `MESSAGE_SENT`, `KB_UPLOAD`, `KB_DELETE`, `ADMIN_CREATED_USER` não são persistidos. Sem trilha de auditoria em produção. Definir modelo `ActivityLog`, schema de eventos e política de retenção (LGPD) quando for implementada.
- [ ] **Contrato de `record` subdeterminado:** metadados como `metadata={...}` vs kwargs posicionais, tipos de evento e obrigatoriedade de `user` só serão fixados com a implementação. Validar com as units consumidoras antes de implementar.

# Audit / Record, Tarefas de Implementação

> Sequência executável para implementar a auditoria a partir do legado.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos

- [ ] Decisão de modelo `ActivityLog` (campos, schema de eventos) — hoje indefinida

## Tarefas

- [ ] **T-01**, Implementar `record(event, *, user=None, **kwargs)` persistindo em `ActivityLog`
  - Origem no legado: `apps/audit/services/log.py:1-4` (stub `pass`)
  - Critério de pronto: grava evento com metadados, sem logar PII (conteúdo de mensagens, dados biométricos)
  - Confiança: 🟢 (contrato); 🟡 (schema)

- [ ] **T-02**, Criar modelo `ActivityLog` com migration
  - Critério de pronto: campos `event`, `user` (FK nullable), `metadata` (JSON), `created_at`; migration commitada
  - Confiança: 🟡

- [ ] **T-03**, Manter rotas admin delegadas (`users/`, `metrics/`) funcionais
  - Origem no legado: `apps/audit/urls.py:6-9`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, `record("GUARDRAIL_BLOCKED", metadata={reason})` persiste registro auditável
- [ ] **TT-02**, Chamadas stub existentes não quebram com a implementação
- [ ] **TT-03**, Metadados não contêm PII (LGPD Art. 11)
- [ ] **TT-04**, `/api/v1/admin/metrics/` segue respondendo para role ADMIN
- [ ] **TT-05**, `/api/v1/admin/knowledge/metrics/` → 404 (rota no urlconf audit)

## Ordem Sugerida

1. T-02 (modelo) → T-01 (service) → T-03 (roteamento).
2. Testes TT-01 a TT-05.

## Lacunas Pendentes (🔴)

- [ ] Definir schema de eventos e política de retenção (LGPD — dados sensíveis).
- [ ] Avaliar cascade delete ao deletar usuário (LGPD Art. 11).
- [ ] Desacoplar rota `metrics` (pertence ao rag) do urlconf do audit.

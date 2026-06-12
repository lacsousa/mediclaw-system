# ~~Epic 3 — Dashboard e Health Logs~~ — DESCONTINUADO

> **Status:** Descontinuado em 2026-05-27 pelo pivot da aplicação.
> **Motivo:** Os formulários de entrada manual de dados biométricos foram removidos da interface. O backend agora extrai dados de saúde automaticamente via NLP das mensagens de chat (`capture_from_message`). Usuários fornecem informações de forma conversacional. Rotas `/dashboard` e `/health/*` não existem mais.
> ~~**Objetivo:** Dashboard de resumo e CRUD completo dos quatro tipos de log biométrico.~~
> ~~**Pré-requisito:** Epic 2 finalizado.~~

---

## Story 3.1 — Dashboard com summary

### `hooks/useHealthSummary.ts`

```typescript
export function useHealthSummary(window: 7 | 30 = 7) {
  // GET /api/v1/health/summary?window={window}
  // retorna { data: HealthSummary | null, isLoading, error }
}
```

### `components/health/SummaryCard.tsx`

Props: `label`, `value`, `unit`, `isLoading`

- Skeleton quando `isLoading`
- Valor `null` exibido como `—`
- Ícone e cor configuráveis por tipo

### `/dashboard/page.tsx`

```
┌─────────────────────────────────────────────────┐
│  Peso médio (7d)  │  Sono médio (7d)  │ Atividade │
│    72,3 kg        │    7,2h (qual. 8) │ 240 min   │
└─────────────────────────────────────────────────┘
  [+ Registrar peso] [+ Registrar sono] [+ Atividade]

  Status da API: ● online  (GET /health)
```

---

## Story 3.2 — Logs de Peso (`/health/weight`)

### `hooks/useHealthLogs.ts`

Interface genérica parametrizada por tipo:

```typescript
export function useHealthLogs(type: "weight" | "sleep" | "activity" | "nutrition") {
  // GET /api/v1/health/{type}?from=&to=
  // POST /api/v1/health/{type}
  // DELETE /api/v1/health/{type}/{id}
}
```

### `components/health/LogForm.tsx`

Campos específicos por tipo via props ou switch interno.

**Peso:**

- `value_kg` — input number (step 0.1)
- `measured_at` — datetime-local, padrão now(), max = now()
- Validação: 20 ≤ value_kg ≤ 400

### `components/health/LogTable.tsx`

- Colunas configuráveis por tipo
- Paginação (botão "Carregar mais" ou paginação numérica)
- Filtro de período: inputs `from` e `to` (date)
- Ação de deletar com `AlertDialog` de confirmação do Chakra

---

## Story 3.3 — Logs de Sono (`/health/sleep`)

**Campos do formulário:**

- `duration_hours` — number (step 0.5), 0 < valor ≤ 24
- `quality_score` — `Slider` Chakra de 1 a 10 com label numérico
- `started_at` — datetime-local

**Coluna especial na tabela:**

- `quality_score` exibido como badge colorido:
  - 1–4: vermelho (`red`)
  - 5–7: amarelo (`yellow`)
  - 8–10: verde (`green`)

---

## Story 3.4 — Logs de Atividade (`/health/activity`)

**Campos do formulário:**

- `type` — `Select` com opções: Caminhada, Corrida, Musculação, Ciclismo, Natação, Yoga, Outro
- `duration_min` — number inteiro, mínimo 1
- `performed_at` — datetime-local

---

## Story 3.5 — Notas de Nutrição (`/health/nutrition`)

**Campos do formulário:**

- `note` — `Textarea` com `maxLength={1000}`, contador de chars exibido abaixo
- `logged_at` — datetime-local, padrão now()

---

## Story 3.6 — Testes Automatizados

### O que fazer

- Garantir testes unitários da renderização dos `SummaryCard`s no Dashboard (inclusive com dados mockados e estados de skeleton).
- Testar a interação do usuário com os formulários de saúde (por exemplo, bloqueio de peso fora do range 20–400 kg).

---

## Critérios de Aceite da Epic

- [x] Dashboard exibe cartões com skeleton durante carregamento
- [x] Valores `null` do summary exibidos como "—" sem crash
- [x] Formulário de peso valida 20–400 kg antes de chamar a API
- [x] Data futura em qualquer formulário é bloqueada client-side
- [x] Delete exibe confirmação antes de chamar a API
- [x] Toast de sucesso/erro após cada operação

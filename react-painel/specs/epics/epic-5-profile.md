# ~~Epic 5 — Perfil do Usuário~~ — DESCONTINUADO

> **Status:** Descontinuado em 2026-05-27 pelo pivot da aplicação.
> **Motivo:** A página `/profile` foi removida. O perfil do usuário (nome, altura, sexo biológico, data de nascimento) é coletado durante o onboarding conversacional. O backend gera automaticamente uma conversa de boas-vindas no cadastro (`ensure_welcome_conversation`) e extrai os dados das respostas via `capture_from_message`. Rota `/profile` não existe mais.
> ~~**Objetivo:** Visualização, edição de perfil e exclusão de conta.~~
> ~~**Pré-requisito:** Epic 2 finalizado.~~

---

## Story 5.1 — Visualizar e editar perfil (`/profile`)

### Campos

| Campo            | Editável | Tipo                                 |
| ---------------- | -------- | ------------------------------------ |
| `email`          | Não      | Text (readonly)                      |
| `name`           | Sim      | Text                                 |
| `birth_date`     | Sim      | Date                                 |
| `biological_sex` | Sim      | Select: Masculino / Feminino / Outro |
| `height_cm`      | Sim      | Number (cm)                          |

### Fluxo

1. Mount → `GET /api/v1/auth/me` preenche o formulário
2. Submit → `PATCH /api/v1/auth/me` com apenas os campos editáveis
3. Sucesso → toast "Perfil atualizado" + atualiza `user` no `AuthContext`
4. Erro → toast com a mensagem do backend

---

## Story 5.2 — Exclusão de conta

### Modal de confirmação

```
┌────────────────────────────────────────────────────────┐
│ ⚠️ Excluir conta                                       │
│                                                        │
│ Esta ação é irreversível. Todos os seus dados          │
│ (conversas, logs de saúde) serão permanentemente       │
│ deletados.                                             │
│                                                        │
│ Digite EXCLUIR para confirmar:                         │
│ [________________________]                             │
│                                                        │
│ [Cancelar]              [Excluir conta] (vermelho)     │
└────────────────────────────────────────────────────────┘
```

- Botão "Excluir conta" desabilitado até que o campo contenha exatamente "EXCLUIR"
- Ao confirmar → `DELETE /api/v1/auth/me` → `logout()` → redirect `/login`

---

## Story 5.3 — Testes Automatizados

### O que fazer

- Testar se a atualização de dados no perfil reflete corretamente no contexto/estado da aplicação.
- Testar se o fluxo do modal de exclusão da conta funciona (bloqueio de submissão incorreta e chamada da API).

---

## Critérios de Aceite da Epic

- [ ] Formulário carregado com dados do usuário autenticado
- [ ] Campo `email` readonly e visualmente diferenciado
- [ ] PATCH salva apenas os campos editáveis e exibe toast de sucesso
- [ ] Modal de exclusão só habilita o botão após digitar "EXCLUIR" exatamente
- [ ] Exclusão faz logout e redireciona para `/login`

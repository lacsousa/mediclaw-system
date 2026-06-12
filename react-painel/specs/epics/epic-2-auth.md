# Epic 2 — Auth

> **Objetivo:** Login, cadastro, proteção de rotas e renovação automática de token.
> **Pré-requisito:** Epic 1 finalizado.

---

## Story 2.1 — Tela de login (`/login`)

### Componente `LoginForm`

Campos:

- `email` — input type `email`, obrigatório
- `password` — input type `password`, obrigatório

Fluxo:

1. Submit → `POST /api/v1/auth/login` com `{ email, password }`
2. Sucesso: `login(tokens, user)` do `AuthContext` → salva em `localStorage` → redirect `/dashboard`
3. Erro `INVALID_CREDENTIALS` → mensagem inline: "E-mail ou senha inválidos"
4. Qualquer outro erro → toast via `ToastContext`

Estado do botão:

- Loading durante a requisição (spinner Chakra)
- Desabilitado durante loading

Link para `/register` no rodapé do formulário.

---

## Story 2.2 — Tela de cadastro (`/register`)

### Componente `RegisterForm`

Campos:

- `name` — obrigatório, mínimo 2 chars
- `email` — type `email`, obrigatório
- `password` — mínimo 8 chars, deve conter letra e dígito
- `confirm_password` — deve ser igual a `password`
- `accept_terms` — checkbox obrigatório

Validações client-side (antes do submit):

```typescript
if (password.length < 8) → "Senha precisa de ao menos 8 caracteres"
if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password)) → "Senha deve conter letra e número"
if (password !== confirm_password) → "Senhas não coincidem"
if (!accept_terms) → "Aceite os termos para continuar"
```

Fluxo:

1. Submit → `POST /api/v1/auth/register` com `{ email, password, name, accept_terms: true }`
2. Sucesso: mesmo fluxo do login
3. `EMAIL_ALREADY_EXISTS` → "Este e-mail já está cadastrado"

---

## Story 2.3 — Proteção de rotas

### Padrão de guard

Cada página privada chama `useAuth()` no topo:

```tsx
// Exemplo: dashboard/page.tsx
export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading]);

  if (isLoading || !isAuthenticated) return <FullPageSpinner />;
  return <PageShell>...</PageShell>;
}
```

### Rotas admin

Verificação adicional em páginas de `/admin/*`:

```tsx
if (!isLoading && user?.role !== "ADMIN") router.replace("/dashboard");
```

### Página raiz (`/`)

```tsx
// app/page.tsx
export default function RootPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      router.replace(isAuthenticated ? "/dashboard" : "/login");
    }
  }, [isAuthenticated, isLoading]);

  return <FullPageSpinner />;
}
```

---

## Story 2.4 — Logout

No `TopBar`:

```tsx
<Button onClick={logout} variant="ghost">
  Sair
</Button>
```

`logout()` em `lib/auth.ts`:

```typescript
export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login"; // hard redirect para limpar estado React
}
```

---

## Story 2.5 — Testes Automatizados

### O que fazer

- Testar a renderização dos formulários de Login e Cadastro.
- Validar se as mensagens de erro client-side aparecem antes do submit.
- Mockar as respostas da API (`msw` ou `jest.mock`) para testar o sucesso (redirect) e erros.

---

## Critérios de Aceite da Epic

- [x] Login com credenciais válidas redireciona para `/dashboard`
- [x] Login com credenciais inválidas exibe erro inline (não toast)
- [x] Cadastro com e-mail duplicado exibe mensagem específica
- [x] Checkbox de termos bloqueante: submit desabilitado se não marcado
- [x] Refresh de página em rota privada: usuário permanece autenticado (hydration do Context)
- [x] Rota privada sem token redireciona para `/login`
- [x] Rota admin com role USER redireciona para `/dashboard`
- [x] Logout limpa tokens e redireciona para `/login`

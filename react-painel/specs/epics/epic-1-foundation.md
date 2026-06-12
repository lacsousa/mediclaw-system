# Epic 1 — Foundation

> **Objetivo:** Estrutura base do projeto: providers, cliente HTTP, layout global e wrapper SSE.
> **Bloqueante:** todos os demais épicos dependem deste.

---

## Contexto

O projeto foi inicializado com Next.js 15, Chakra UI v3 e Axios (`@/lib/api`). O layout root e os providers já têm esqueleto em `src/app/layout.tsx` e `src/components/providers.tsx`. Esta epic finaliza a infraestrutura antes de qualquer tela de negócio.

---

## Story 1.1 — Providers e layout root

### O que fazer

Criar `AuthContext` e `ToastContext` e integrá-los ao `layout.tsx` root junto com o `ChakraProvider` já existente.

### `context/AuthContext.tsx`

```tsx
interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (tokens: { access: string; refresh: string }, user: User) => void;
  logout: () => void;
}
```

- No mount, lê `localStorage.getItem("access_token")` e chama `GET /api/v1/auth/me` para hidratar `user`
- Se o request falhar (token expirado), tenta refresh; se ainda falhar, limpa o storage
- `isLoading=true` enquanto a hidratação acontece (evita flash de redirect)

### `context/ToastContext.tsx`

```tsx
interface ToastContextValue {
  showToast: (message: string, status: "success" | "error" | "info" | "warning") => void;
}
```

Usa o `useToast` do Chakra internamente.

---

## Story 1.2 — Cliente HTTP com interceptors JWT

### `lib/api.ts`

```typescript
import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "",
});

// Request: injeta token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response: trata 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const refreshed = await refreshToken(); // lib/auth.ts
      if (refreshed) {
        error.config.headers.Authorization = `Bearer ${localStorage.getItem("access_token")}`;
        return api(error.config);
      }
      logout(); // limpa e redireciona
    }
    return Promise.reject(error);
  }
);
```

### `lib/auth.ts`

```typescript
export async function refreshToken(): Promise<boolean> { ... }
export function logout(): void { ... }
```

### `types/api.ts`

Definir as interfaces principais conforme listado em [ARCHITECTURE.md](../ARCHITECTURE.md).

---

## Story 1.3 — Layout global com navegação

### Estrutura de componentes

```
components/layout/
├── PageShell.tsx   → recebe children; aplica sidebar + topbar + <main>
├── Sidebar.tsx     → lista de links com ícones e highlight de rota ativa
└── TopBar.tsx      → avatar/nome do usuário + botão logout
```

### Itens de navegação

```typescript
const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: HomeIcon },
  { label: "Peso", href: "/health/weight", icon: ScaleIcon },
  { label: "Sono", href: "/health/sleep", icon: MoonIcon },
  { label: "Atividade", href: "/health/activity", icon: ActivityIcon },
  { label: "Nutrição", href: "/health/nutrition", icon: LeafIcon },
  { label: "Chat IA", href: "/chat", icon: ChatIcon },
  { label: "Perfil", href: "/profile", icon: UserIcon },
];

const adminItems = [
  { label: "Base de Conhecimento", href: "/admin/knowledge", icon: BookIcon },
  { label: "Métricas", href: "/admin/metrics", icon: BarChartIcon },
];
```

### Responsividade

- Desktop (≥ `md`): sidebar fixa à esquerda (240px), main com `marginLeft`
- Mobile (< `md`): sidebar em `Drawer` do Chakra, aberto via botão hamburger na topbar

---

## Story 1.4 — Wrapper SSE

### `lib/sse.ts`

```typescript
interface SSECallbacks {
  onToken: (content: string) => void;
  onCitation: (citation: { source: string; chunk_id: string }) => void;
  onDone: (result: { tokens_used: number; blocked: boolean }) => void;
  onError: (error: { code: string; message: string }) => void;
}

export function openStream(url: string, callbacks: SSECallbacks): () => void {
  const es = new EventSource(url);

  es.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case "token":
        callbacks.onToken(data.content);
        break;
      case "citation":
        callbacks.onCitation(data);
        break;
      case "done":
        callbacks.onDone(data);
        es.close();
        break;
      case "error":
        callbacks.onError(data);
        es.close();
        break;
    }
  };

  es.onerror = () => {
    callbacks.onError({ code: "SSE_ERROR", message: "Conexão interrompida" });
    es.close();
  };

  return () => es.close(); // cleanup
}
```

---

## Story 1.5 — Testes Automatizados

### O que fazer

- Testar a renderização do `PageShell` e a proteção de rotas privadas.
- Garantir que o `AuthContext` hidrata o usuário corretamente a partir do `localStorage` e gerencia estados de loading.

---

## Critérios de Aceite da Epic

- [x] `npm run dev` sobe sem erros de TypeScript ou ESLint
- [x] `AuthContext` hidrata usuário do localStorage no refresh de página
- [x] Interceptor renova token e reenvia request transparentemente
- [x] Sidebar colapsa em drawer em viewport mobile
- [x] Links de admin visíveis apenas para role ADMIN
- [x] `openStream` fecha EventSource ao chamar a função de cleanup

# Epic 4 — Chat com IA

> **Objetivo:** Interface de conversas com streaming SSE, exibição de guardrails e citações.
> **Pré-requisito:** Epic 2 finalizado; Epic 1 (lib/sse.ts) concluído.

---

## Story 4.1 — Lista de conversas (`/chat`)

### `hooks/useConversations.ts`

```typescript
export function useConversations() {
  // GET  /api/v1/conversations
  // POST /api/v1/conversations → { id, title, created_at }
  // DELETE /api/v1/conversations/{id}
}
```

### Layout da página

```
┌────────────────────────────────────────┐
│  Minhas Conversas         [+ Nova]     │
├────────────────────────────────────────┤
│  [Sem título]    há 2 horas       [🗑] │
│  [Como melhorar meu sono?] há 1d  [🗑] │
│  ...                                   │
│             [Carregar mais]            │
└────────────────────────────────────────┘
```

- Cada item leva para `/chat/{id}`
- "Nova conversa": `POST /api/v1/conversations` → redirect `/chat/{id}`
- Delete com `AlertDialog` de confirmação

---

## Story 4.2 — Carregamento do histórico (`/chat/[id]`)

### `hooks/useMessages.ts`

```typescript
export function useMessages(conversationId: number) {
  // GET /api/v1/conversations/{id}
  // retorna { conversation, messages, isLoading }
}
```

### `components/chat/MessageBubble.tsx`

Props: `message: Message`

```
┌─────────────────────────────────────────────────────┐
│                          [Usuário: texto da pergunta]│  ← direita, cor primária
│ [Assistente: resposta da IA]                         │  ← esquerda, cor neutra
│ ℹ Esta orientação é educativa e não substitui um     │
│   profissional de saúde.                 [disclaimerr]│
│ 📚 Fonte: Sleep Foundation 2024         [citation]   │
└─────────────────────────────────────────────────────┘
```

- Role `ASSISTANT` → disclaimer sempre visível abaixo da bolha
- `blocked_by_guardrail=true` → badge vermelho "Resposta limitada" no topo da bolha
- Citações em `message.metadata.citations` → lista de `CitationBadge`

---

## Story 4.3 — Streaming SSE

### `components/chat/ChatInput.tsx`

Estado interno:

```typescript
const [input, setInput] = useState("");
const [isStreaming, setIsStreaming] = useState(false);
const [partialReply, setPartialReply] = useState("");
const [citations, setCitations] = useState<Citation[]>([]);
const cleanupRef = useRef<(() => void) | null>(null);
```

Fluxo ao submeter:

```
1. setIsStreaming(true)
2. Adiciona bolha do usuário otimisticamente no estado local
3. Adiciona bolha parcial do assistente (partialReply = "")
4. Abre SSE via openStream(url, callbacks):
   - onToken:    setPartialReply(prev => prev + content)
   - onCitation: setCitations(prev => [...prev, citation])
   - onDone:     setIsStreaming(false); fetchMessages() (recarrega histórico completo)
   - onError:    setIsStreaming(false); showToast(message, "error")
5. Guarda cleanup em cleanupRef
```

Cleanup ao desmontar:

```typescript
useEffect(() => {
  return () => cleanupRef.current?.();
}, []);
```

### URL do SSE

```typescript
const token = localStorage.getItem("access_token");
const prompt = encodeURIComponent(input);
const url = `${process.env.NEXT_PUBLIC_API_URL}conversations/${id}/stream?prompt=${prompt}&token=${token}`;
```

### Animação de cursor

Enquanto `isStreaming`, a bolha parcial exibe um cursor `|` piscando via CSS:

```css
.typing-cursor::after {
  content: "|";
  animation: blink 1s step-end infinite;
}
```

---

## `components/chat/CitationBadge.tsx`

```tsx
// Exibe badge discreto com o nome da fonte
<Badge colorPalette="blue" size="sm">
  📚 {source}
</Badge>
```

---

## Story 4.4 — Testes Automatizados

### O que fazer

- Testar a renderização correta das mensagens no chat.
- Garantir o tratamento do evento de streaming SSE no UI (adição progressiva de tokens).

---

## Critérios de Aceite da Epic

- [ ] Lista de conversas carrega e pagina corretamente
- [ ] "Nova conversa" cria e redireciona para `/chat/{id}`
- [ ] Histórico existente exibe mensagens anteriores ao abrir o chat
- [ ] Tokens aparecem progressivamente durante o streaming (não de uma vez)
- [ ] Cursor piscante visível durante streaming
- [ ] Evento `citation` exibe badge de fonte abaixo da bolha
- [ ] `blocked=true` exibe badge "Resposta limitada" com cor vermelha
- [ ] Disclaimer visível abaixo de toda bolha do assistente
- [ ] Input desabilitado durante streaming
- [ ] Fechar a aba durante streaming não vaza EventSource (cleanup no unmount)
- [ ] Erro de SSE exibe toast sem travar o input

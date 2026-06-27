# Notes — MediClaw

## Como rodar os testes

### Backend (Django)

```bash
cd django-api

# Rodar todos os testes
uv run pytest

# Rodar um módulo específico
uv run pytest tests/rag/
uv run pytest tests/ai_engine/

# Com verbose e traceback curto
uv run pytest -v --tb=short
```

Os testes ficam em `django-api/tests/`, organizados por app: `accounts/`, `rag/`, `ai_engine/`, `conversations/`, `health_logs/`, etc.

### Frontend (Next.js / Vitest)

```bash
cd react-painel

# Rodar uma vez
npm test

# Watch mode (re-roda ao salvar)
npx vitest
```

Os testes ficam em `react-painel/src/__tests__/components/`.

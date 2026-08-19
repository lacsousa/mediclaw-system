# Dependências — MediClaw

> Gerado pelo **Scout** em 2026-08-19.
> Fontes: `django-api/pyproject.toml` (autoritativo, uv) e `react-painel/package.json`.

## 1. Backend (`django-api`) — Python 3.12, gerenciador `uv`

### Dependências de produção (declaradas em `pyproject.toml`)

| Pacote | Versão | Papel |
|---|---|---|
| Django | 5.2.1 | Framework web |
| djangorestframework | 3.16.0 | REST API |
| djangorestframework-simplejwt | 5.5.0 | Auth JWT (access + refresh) |
| psycopg[binary] | 3.2.13 | Driver PostgreSQL |
| python-dotenv | 1.1.0 | Variáveis de ambiente |
| django-cors-headers | 4.7.0 | CORS |
| pypdf | >=4.0 | Leitura de PDFs (RAG) |
| pydantic | >=2.7 | Schemas/validação |
| chromadb | 0.5.* | Vector store (RAG) |
| langchain | 0.3.* | Orquestração/RAG |
| langchain-openai | 0.3.* | Provider OpenAI |
| langchain-google-genai | 2.* | Provider Gemini |
| langchain-community | 0.3.* | Integrações LangChain |
| openai | >=1.30 | SDK OpenAI |
| google-genai | >=1.0 | SDK Google Gemini |
| uvicorn[standard] | >=0.30 | Servidor ASGI |
| drf-yasg | 1.21.15 | OpenAPI/Swagger |

### Dependências de desenvolvimento

| Pacote | Versão | Papel |
|---|---|---|
| pytest | 8.* | Testes |
| pytest-django | 4.* | Integração pytest/Django |
| freezegun | >=1.5.0 | Controle de tempo nos testes |
| pre-commit | 4.2.0 | Hooks de qualidade |
| black | 25.1.0 | Formatação |
| structlog | >=26.1.0 | Logging estruturado |

### Dependências transitivas relevantes (do lock `requirements.txt`)

- `aiohttp`, `aiohappyeyeballs` — cliente HTTP (LangChain)
- `cryptography`, `bcrypt` — hashing/criptografia
- `httpx`, `anyio` — HTTP async (SDKs OpenAI/Gemini)
- `kubernetes` — via langchain-community
- `fastapi`, `uvicorn` — runtime do ChromaDB
- `google-ai-generativelanguage`, `google-api-python-client` — stack Google
- `onnxruntime` — via chromadb
- `posthog` — telemetria (anônima, desativável)

## 2. Frontend (`react-painel`) — Node >= 20, gerenciador `npm`

### Dependências de produção

| Pacote | Versão | Papel |
|---|---|---|
| next | 16.2.4 | Framework React (App Router, build standalone) |
| react | 19.2.4 | UI |
| react-dom | 19.2.4 | Renderização |
| @chakra-ui/react | ^3.35.0 | Design system de componentes |
| @emotion/react | ^11.14.0 | Estilização (base Chakra) |
| axios | ^1.15.2 | HTTP client (com interceptor JWT + refresh) |
| react-markdown | ^10.1.0 | Renderização de respostas em Markdown |
| remark-gfm | ^4.0.1 | Tabelas/listas GFM no Markdown |

### Dependências de desenvolvimento

| Pacote | Versão | Papel |
|---|---|---|
| typescript | ^5 | Tipagem |
| eslint | ^9 | Lint |
| eslint-config-next | 16.2.4 | Regras Next.js |
| prettier | ^3.6.2 | Formatação |
| vitest | ^4.1.7 | Runner de testes |
| @vitejs/plugin-react | ^6.0.2 | JSX nos testes |
| jsdom | ^29.1.1 | Ambiente DOM nos testes |
| @testing-library/react | ^16.3.2 | Testes de componentes |
| @testing-library/jest-dom | ^6.9.1 | Matchers DOM |
| @testing-library/user-event | ^14.6.1 | Interação de usuário |
| husky | ^9.1.7 | Git hooks |
| lint-staged | ^15.5.2 | Lint em staged files |
| @types/node, @types/react, @types/react-dom | — | Tipos |

## 3. Infraestrutura

| Componente | Versão/Detalhe | Local |
|---|---|---|
| PostgreSQL | 16 (imagem `pgvector/pgvector:pg16`) | `docker-compose.prod.yml` |
| Nginx | Sistema (apt), não containerizado | `nginx/system/*.conf` |
| Certbot / Let's Encrypt | TLS | `nginx/init-letsencrypt.sh` |
| Docker | compose v2 | repo raiz |

## 4. Notas

- 🟢 O `requirements.txt` é um lock export do `uv` (com hashes) — `pyproject.toml` é a fonte declarativa.
- 🟢 Frontend usa `next build --webpack` (webpack em vez do turbopack, ver scripts do `package.json`).
- 🟡 O projeto real não usa os providers Anthropic previstos nas specs — apenas OpenAI e Gemini estão implementados.

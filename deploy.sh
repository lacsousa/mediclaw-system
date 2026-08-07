#!/bin/bash
# deploy.sh
# Automatiza o deploy de uma nova versão do MediClaw no VPS (mediclaw.com.br).
# Roda a partir de /opt/mediclaw no servidor (ver DEPLOY.md).
#
# A landing page (marketing/landing/index.html) é HTML estático servido
# direto pelo Nginx do sistema a partir desta mesma pasta do repo — o
# "git pull" abaixo já é suficiente para publicar mudanças nela. Não há
# build, container ou reload de Nginx envolvidos para atualizar só o
# conteúdo da landing.
#
# Uso:
#   ./deploy.sh              # deploy normal
#   ./deploy.sh --skip-tests # pula pytest/vitest (não recomendado)
#   ./deploy.sh --skip-prune # não remove imagens Docker antigas ao final

set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
SKIP_TESTS=false
SKIP_PRUNE=false

for arg in "$@"; do
  case "$arg" in
    --skip-tests) SKIP_TESTS=true ;;
    --skip-prune) SKIP_PRUNE=true ;;
    -h|--help)
      echo "Uso: $0 [--skip-tests] [--skip-prune]"
      exit 0
      ;;
    *)
      echo "❌ Argumento desconhecido: $arg"
      exit 1
      ;;
  esac
done

# Garante que o script roda a partir da raiz do repo, seja qual for o cwd.
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Iniciando deploy do MediClaw..."

echo "🔎 0. Checando pré-requisitos..."

if [ ! -f .env ]; then
  echo "❌ Falta .env na raiz (copie de .env.production.example). Abortando."
  exit 1
fi
if [ ! -f django-api/.env.production ]; then
  echo "❌ Falta django-api/.env.production (copie de .env.production.example). Abortando."
  exit 1
fi
# --untracked-files=no: "staticfiles/" e afins são gerados no servidor e
# aparecem como untracked — não são motivo para abortar. O que importa é não
# ter edição local em arquivo versionado, que o git pull sobrescreveria.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "❌ Há mudanças locais em arquivos versionados no servidor. Resolva antes (git status)."
  exit 1
fi

echo "📦 1. Puxando as atualizações mais recentes do Git..."
git pull

if [ "$SKIP_TESTS" = false ]; then
  echo "🧪 2. Rodando testes antes do build..."
  if command -v uv >/dev/null 2>&1 && [ -d django-api ]; then
    (cd django-api && uv run pytest) || { echo "❌ Testes do django-api falharam. Abortando deploy."; exit 1; }
  else
    echo "⚠️  uv não encontrado — pulando testes do django-api."
  fi
  if command -v npm >/dev/null 2>&1 && [ -d react-painel ]; then
    (cd react-painel && npm run test) || { echo "❌ Testes do react-painel falharam. Abortando deploy."; exit 1; }
  else
    echo "⚠️  npm não encontrado — pulando testes do react-painel."
  fi
else
  echo "⏭️  2. Testes pulados (--skip-tests)."
fi

echo "🛠️  3. Construindo as imagens e recriando os containers..."
$COMPOSE build
$COMPOSE up -d postgres django-api react-painel

echo "🩺 4. Verificando saúde dos serviços..."
# O Django recusa Host desconhecido (ALLOWED_HOSTS) com 400 e redireciona
# http->https (SECURE_SSL_REDIRECT) com 301. Bater direto em 127.0.0.1 sem
# forjar os headers dá falso negativo — daí o "-H Host" e o
# "X-Forwarded-Proto: https", mesmo truque do HEALTHCHECK do Dockerfile.
wait_for() {
  local name="$1" url="$2" tries=30
  shift 2
  for ((i = 1; i <= tries; i++)); do
    if curl -sf -o /dev/null "$@" "$url"; then
      echo "   ✅ $name respondendo ($url)"
      return 0
    fi
    sleep 2
  done
  echo "   ❌ $name não respondeu em $((tries * 2))s ($url)."
  echo "      Veja: $COMPOSE logs --tail=100 $name"
  return 1
}

$COMPOSE ps
wait_for django-api "http://127.0.0.1:8000/health/" \
  -H "Host: api.mediclaw.com.br" -H "X-Forwarded-Proto: https" || exit 1
wait_for react-painel "http://127.0.0.1:3001" || exit 1

if [ "$SKIP_PRUNE" = false ]; then
  echo "🧹 5. Limpando imagens antigas sem uso para liberar espaço no VPS..."
  docker image prune -f
else
  echo "⏭️  5. Prune pulado (--skip-prune)."
fi

echo "🎉 Deploy concluído com sucesso!"
echo "➡️  Painel:  https://www.mediclaw.com.br"
echo "➡️  Landing: https://mediclaw.com.br"
echo "➡️  API:     https://api.mediclaw.com.br/health/"
echo "➡️  Logs:    $COMPOSE logs -f"

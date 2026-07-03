#!/bin/sh
# django-api/entrypoint.prod.sh
# Roda migrações e coleta os estáticos antes de subir o Uvicorn.
# Referenciado pelo docker-compose.prod.yml (não faz parte da imagem para
# não travar o build caso o Postgres ainda não esteja de pé).
set -e

echo "[entrypoint] Aguardando Postgres em ${DB_HOST:-postgres}:${DB_PORT:-5432}..."
until python -c "
import os, socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((os.environ.get('DB_HOST', 'postgres'), int(os.environ.get('DB_PORT', 5432))))
except OSError:
    sys.exit(1)
"; do
  sleep 1
done

echo "[entrypoint] Rodando migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Coletando estáticos..."
python manage.py collectstatic --noinput

echo "[entrypoint] Subindo Uvicorn..."
exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-3}"

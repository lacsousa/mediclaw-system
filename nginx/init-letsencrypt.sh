#!/usr/bin/env bash
# ⚠️ NÃO USADO NESTE DEPLOY — mantido só como referência.
# Este VPS já roda outro projeto (llmscout.tech) com Nginx do SISTEMA +
# Certbot próprio nas portas 80/443. Por isso o MediClaw usa as configs em
# nginx/system/ (aplicadas no Nginx do host), não este container Nginx
# dockerizado. Ver DEPLOY.md, seção "1. Nginx do sistema".

# nginx/init-letsencrypt.sh
#
# Bootstrap dos certificados Let's Encrypt na primeira subida do stack.
# Só precisa rodar UMA vez (a renovação automática já é feita pelo serviço
# "certbot" do docker-compose.prod.yml, que roda em loop).
#
# Pré-requisitos:
#   - DNS de mediclaw.com.br, www.mediclaw.com.br e api.mediclaw.com.br
#     já apontando (registro A) para o IP deste VPS.
#   - postgres, django-api e react-painel já no ar:
#       docker compose -f docker-compose.prod.yml up -d postgres django-api react-painel
#   - Rodar a partir da raiz do repo: ./nginx/init-letsencrypt.sh
#
# Padrão: sobe certificados "dummy" (autoassinados) só para o Nginx
# conseguir iniciar e servir o desafio ACME, pede os certificados reais via
# webroot, e recarrega o Nginx.

set -euo pipefail

COMPOSE=(docker compose -f docker-compose.prod.yml)
EMAIL="${LETSENCRYPT_EMAIL:?defina LETSENCRYPT_EMAIL=voce@exemplo.com antes de rodar}"
STAGING="${STAGING:-0}"   # STAGING=1 para testar sem esbarrar no rate limit do Let's Encrypt

# domínio-principal:demais-SANs do mesmo certificado (SANs vazio = sem extra)
CERTS=(
  "mediclaw.com.br:www.mediclaw.com.br"
  "api.mediclaw.com.br:"
)

run_sh() {
  # Roda um script shell dentro do container certbot (entrypoint sobrescrito
  # para "sh", o script vai como argumento de -c).
  "${COMPOSE[@]}" run --rm --entrypoint sh certbot -c "$1"
}

echo "==> Gerando certificados dummy para o Nginx conseguir subir..."
for entry in "${CERTS[@]}"; do
  domain="${entry%%:*}"
  run_sh "
    mkdir -p /etc/letsencrypt/live/$domain
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout /etc/letsencrypt/live/$domain/privkey.pem \
      -out /etc/letsencrypt/live/$domain/fullchain.pem \
      -subj '/CN=localhost'
  "
done

echo "==> Gerando options-ssl-nginx.conf e ssl-dhparams.pem (uma vez)..."
run_sh "
  test -f /etc/letsencrypt/ssl-dhparams.pem || openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048
  printf '%s\n' \
    'ssl_protocols TLSv1.2 TLSv1.3;' \
    'ssl_prefer_server_ciphers off;' \
    'ssl_session_cache shared:le_nginx_SSL:10m;' \
    'ssl_session_timeout 1440m;' \
    'ssl_session_tickets off;' \
    > /etc/letsencrypt/options-ssl-nginx.conf
"

echo "==> Subindo Nginx (com os certificados dummy)..."
"${COMPOSE[@]}" up -d nginx

echo "==> Apagando certificados dummy e pedindo os certificados reais..."
for entry in "${CERTS[@]}"; do
  domain="${entry%%:*}"
  extra="${entry#*:}"

  run_sh "rm -rf /etc/letsencrypt/live/$domain /etc/letsencrypt/archive/$domain /etc/letsencrypt/renewal/$domain.conf"

  domain_args=(-d "$domain")
  if [ -n "$extra" ]; then
    domain_args+=(-d "$extra")
  fi

  staging_args=()
  if [ "$STAGING" = "1" ]; then
    staging_args+=(--staging)
  fi

  "${COMPOSE[@]}" run --rm --entrypoint certbot certbot certonly \
    --webroot -w /var/www/certbot \
    "${staging_args[@]}" \
    "${domain_args[@]}" \
    --email "$EMAIL" --agree-tos --no-eff-email --force-renewal
done

echo "==> Recarregando Nginx com os certificados reais..."
"${COMPOSE[@]}" exec nginx nginx -s reload

echo "==> Concluído. Verifique https://mediclaw.com.br e https://api.mediclaw.com.br/health/"

# Deploy do MediClaw — mediclaw.com.br (VPS Hostinger)

Guia para colocar o monorepo (`django-api` + `react-painel`) no ar no domínio
`mediclaw.com.br`, hospedado no VPS Hostinger (`srv1762478.hstgr.cloud`,
IP `187.77.51.175`).

> **Este VPS também hospeda outro projeto (llmscout.tech).** O Nginx do
> SISTEMA (instalado via `apt`) já ocupa as portas 80/443 com Certbot próprio
> para aquele domínio. Por isso o MediClaw **não** roda seu próprio container
> Nginx/Certbot — django-api e react-painel publicam portas só em
> `127.0.0.1`, e quem termina TLS e faz proxy reverso é o Nginx do sistema,
> com configs adicionais em `nginx/system/`. Se um dia o llmscout sair desse
> VPS, dá para voltar a usar o container `nginx` do compose — mas hoje os
> dois moram na mesma máquina.

## Arquitetura

```
                              ┌───────────────────────────┐
 Internet ── 80/443 ──▶  Nginx DO SISTEMA (apt, TLS)      │
                              │  ├─ mediclaw.com.br       │──▶ 127.0.0.1:3001 (react-painel)
                              │  ├─ api.mediclaw.com.br   │──▶ 127.0.0.1:8000 (django-api)
                              │  └─ llmscout.tech         │──▶ 127.0.0.1:? (outro projeto)
                              └───────────────────────────┘
                                          │
                                    django-api ──▶ postgres:5432 (pgvector/pg16, container)
                                          └──▶ chroma_data/ (volume, RAG)
```

Subdomínios (decisão já tomada): `mediclaw.com.br` serve o painel Next.js,
`api.mediclaw.com.br` serve a API Django. O Certbot do SISTEMA (o mesmo que já
renova o certificado do llmscout) cuida da renovação automática.

Todos os arquivos abaixo já foram criados no repositório:

| Arquivo | Papel |
|---|---|
| `docker-compose.prod.yml` | Orquestra postgres, django-api, react-painel (sem nginx/certbot) |
| `django-api/Dockerfile.prod` | Build de produção do Django (uv + Uvicorn) |
| `django-api/entrypoint.prod.sh` | Roda `migrate` + `collectstatic` antes de subir o Uvicorn |
| `react-painel/Dockerfile.prod` | Build de produção do Next.js (`output: "standalone"`) |
| `nginx/system/*.conf` | Configs para o Nginx DO SISTEMA (copiar para `/etc/nginx/sites-available/`) |
| `nginx/conf.d/*.conf`, `nginx/init-letsencrypt.sh` | ⚠️ Não usados neste deploy — só referência (arquitetura com Nginx dockerizado, caso o llmscout saia do VPS) |
| `django-api/.env.production.example` | Template de env vars da API |
| `.env.production.example` | Template de env vars do compose (Postgres, build do painel) |

---

## 1. DNS no registro.br

No painel do registro.br (`registro.br/painel/dominios`), abra
`mediclaw.com.br` → **Editar Zona DNS** (ou "Configurar DNS") e crie os
registros:

| Tipo | Nome | Valor | TTL |
|---|---|---|---|
| A | `@` (mediclaw.com.br) | `187.77.51.175` | 3600 |
| A | `www` | `187.77.51.175` | 3600 |
| A | `api` | `187.77.51.175` | 3600 |

Propagação costuma levar de alguns minutos a poucas horas. Confirme antes de
seguir para o passo 4 (emissão de certificado exige que o DNS já resolva):

```bash
dig +short mediclaw.com.br
dig +short api.mediclaw.com.br
# ambos devem responder 187.77.51.175
```

---

## 2. Preparar o VPS

Acesse via SSH (painel Hostinger → VPS → Manage → mostra usuário/IP, ou use
o terminal do navegador da Hostinger):

```bash
ssh root@187.77.51.175
```

Instale Docker + Docker Compose plugin (Ubuntu):

```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin git
```

Firewall — libere só o essencial:

```bash
apt install -y ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

(Opcional, mas recomendado): crie um usuário não-root para operar o deploy e
adicione-o ao grupo `docker`, em vez de usar `root` no dia a dia.

---

## 3. Clonar o repositório no servidor

```bash
mkdir -p /opt/mediclaw && cd /opt/mediclaw
git clone <url-do-seu-repo-git> .
```

Se o repositório ainda não está em um Git remoto, suba-o para o GitHub
primeiro — é o jeito mais simples de manter o VPS atualizado com `git pull`.
Alternativa sem Git remoto: `rsync -avz --exclude node_modules --exclude .venv ./ root@187.77.51.175:/opt/mediclaw/`.

---

## 4. Variáveis de ambiente de produção

No servidor, a partir dos templates já commitados:

```bash
cd /opt/mediclaw
cp .env.production.example .env
cp django-api/.env.production.example django-api/.env.production
```

> O arquivo da raiz precisa se chamar exatamente `.env` — é o nome que o
> `docker compose` procura automaticamente para interpolar variáveis como
> `${DB_PASSWORD}` dentro do `docker-compose.prod.yml`.

Edite os dois arquivos (`nano .env`, `nano django-api/.env.production`):

- **`.env`** (raiz): `DB_PASSWORD` (senha forte), `LETSENCRYPT_EMAIL`
  (seu e-mail real, usado para avisos de expiração de certificado).
- **`django-api/.env.production`**:
  - `SECRET_KEY` — gere com `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
  - `DB_PASSWORD` — **igual** ao definido no `.env` da raiz
  - `OPENAI_API_KEY` (ou `GOOGLE_API_KEY` se usar Gemini) — chave real do provedor de IA
  - `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` já vêm
    pré-preenchidos com `mediclaw.com.br` / `api.mediclaw.com.br` — só ajuste
    se usar outros subdomínios.

Nenhum desses dois arquivos deve ir para o Git (`.env` e `.env.production` já
estão no `.gitignore`).

---

## 5. Subir o stack de containers

```bash
cd /opt/mediclaw

# pasta de staticfiles é bind mount (não volume nomeado) — o Docker cria
# como root se não existir, mas o container roda como usuário "django"
# (uid 1000). Sem isto, collectstatic falha com PermissionError.
mkdir -p staticfiles
chown -R 1000:1000 staticfiles

# build das imagens de produção
docker compose -f docker-compose.prod.yml build

# sobe postgres + django-api + react-painel
# (sem nginx/certbot — o Nginx é o do SISTEMA, configurado no passo 5b)
docker compose -f docker-compose.prod.yml up -d postgres django-api react-painel

docker compose -f docker-compose.prod.yml ps   # confirme os 3 containers "Up"
curl -I http://127.0.0.1:3001                  # react-painel respondendo (3001: 3000 é do llmscout)
curl -I http://127.0.0.1:8000/health/          # django-api respondendo
```

## 5b. Configurar o Nginx do sistema + certificados TLS

O VPS já roda Nginx (`apt`) para o llmscout.tech — não subimos um Nginx
dockerizado à parte, só adicionamos os vhosts do MediClaw ao Nginx existente.

```bash
cd /opt/mediclaw

# copia os vhosts (ainda sem SSL) para o Nginx do sistema
cp nginx/system/mediclaw.com.br.conf /etc/nginx/sites-available/mediclaw.com.br
cp nginx/system/api.mediclaw.com.br.conf /etc/nginx/sites-available/api.mediclaw.com.br
ln -s /etc/nginx/sites-available/mediclaw.com.br /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/api.mediclaw.com.br /etc/nginx/sites-enabled/

nginx -t && systemctl reload nginx   # confere sintaxe antes de seguir
```

Emita os certificados com o mesmo Certbot já usado para o llmscout (ele edita
os vhosts automaticamente para adicionar o bloco 443/SSL e o redirect
80→443):

```bash
certbot --nginx -d mediclaw.com.br -d www.mediclaw.com.br
certbot --nginx -d api.mediclaw.com.br
```

Ao final, `https://mediclaw.com.br` e `https://api.mediclaw.com.br/health/`
devem responder com cadeado válido. Confirme também que `curl -I https://llmscout.tech`
continua funcionando (o `nginx -t` do passo anterior já teria acusado erro de
sintaxe se algo tivesse quebrado, mas vale conferir na prática).

> A renovação automática já é cuidada pelo timer/serviço `certbot` do
> sistema (o mesmo que renova o llmscout) — não precisa configurar nada novo
> para isso.

---

## 6. Pós-deploy

Criar um superusuário para acessar `/admin/`:

```bash
docker compose -f docker-compose.prod.yml exec django-api python manage.py createsuperuser
```

A base de conhecimento do RAG é indexada via API, não por management
command: `POST /api/v1/admin/knowledge/upload/` (autenticado, ver
`apps/rag/urls.py` e `apps/rag/views.py`). O volume `chroma_data` é
persistente entre deploys — o que já foi indexado continua disponível após
cada `docker compose up`.

---

## 7. Operação do dia a dia

**Deploy de uma nova versão:**

```bash
cd /opt/mediclaw
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

O `entrypoint.prod.sh` do Django roda `migrate` e `collectstatic`
automaticamente a cada subida do container.

**Logs:**

```bash
docker compose -f docker-compose.prod.yml logs -f django-api
docker compose -f docker-compose.prod.yml logs -f react-painel
journalctl -u nginx -f   # Nginx é do sistema, não roda em container aqui
```

**Backup do Postgres** (dados de saúde são dados sensíveis pela LGPD — automatize e
criptografe o destino do backup):

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres mediclaw | gzip > backup-$(date +%F).sql.gz
```

Considere agendar isso via `cron` e enviar para um storage externo (não deixar
só no próprio VPS).

**Renovação de certificado:** já é automática — o Certbot do SISTEMA (o
mesmo timer/serviço que já renova o llmscout.tech) cuida disso para
mediclaw.com.br e api.mediclaw.com.br também. Não precisa de ação manual.
Para testar: `certbot renew --dry-run`.

---

## 8. Checklist de segurança / LGPD

- [ ] `SECRET_KEY` de produção é única e não é a de desenvolvimento
- [ ] `DEBUG=False` em `django-api/.env.production`
- [ ] Firewall (`ufw`) só libera 22/80/443
- [ ] SSH com chave pública; considerar desabilitar login por senha (`PasswordAuthentication no` em `/etc/ssh/sshd_config`)
- [ ] Backups do Postgres agendados e armazenados fora do VPS
- [ ] `.env` (raiz) e `django-api/.env.production` fora do Git, com permissão restrita (`chmod 600`)
- [ ] Confirmar que os logs de produção não gravam PII (já é convenção do projeto — ver `CLAUDE.md`)

---

## Troubleshooting

- **`mediclaw.com.br` abre outro site (ex.: llmscout.tech)**: sintoma de que
  não existe (ou não está habilitado) um vhost com
  `server_name mediclaw.com.br` no Nginx do sistema — o Nginx cai no
  primeiro `server` que escuta na 443 (ou no `default_server`). Confira com
  `nginx -T | grep -A2 server_name` e `ls /etc/nginx/sites-enabled/`; garanta
  que `mediclaw.com.br` e `api.mediclaw.com.br` estão symlinkados em
  `sites-enabled/` e que `nginx -t` não acusa erro.
- **Certbot falha com "connection refused"**: DNS ainda não propagou, ou a
  porta 80 está bloqueada no firewall/Hostinger. Confirme com `dig` e `curl -I http://mediclaw.com.br`.
- **502 Bad Gateway no Nginx**: `django-api` ou `react-painel` ainda não
  subiram / falharam no build, ou não estão escutando em 127.0.0.1:8000 /
  127.0.0.1:3001 (3000 é do llmscout, não usar). Veja
  `docker compose -f docker-compose.prod.yml ps`, os logs do serviço com
  problema, e `curl -I http://127.0.0.1:3001` /
  `curl -I http://127.0.0.1:8000/health/` direto no VPS.
- **"CSRF verification failed" no admin do Django**: confira se
  `CSRF_TRUSTED_ORIGINS` em `django-api/.env.production` inclui
  `https://api.mediclaw.com.br` (com `https://`, não só o domínio nu).
- **Redirect loop em HTTPS**: geralmente falta `SECURE_PROXY_SSL_HEADER` — já
  está configurado em `config/settings.py`, mas confirme que o Nginx do
  sistema está enviando `X-Forwarded-Proto` (já incluso nos confs em
  `nginx/system/`, adicionado automaticamente pelo Certbot ao gerar o bloco
  SSL).

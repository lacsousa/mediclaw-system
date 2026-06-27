# Resumo de Comandos do UV

## Criar ambiente virtual

- `curl -LsSf https://astral.sh/uv/install.sh | sh` - Install UV

- `uv init`: Inicializa um novo projeto gerenciado pelo uv, criando o ambiente virtual e arquivos de configuração (como `pyproject.toml`).
- `uv venv`: Cria um novo ambiente virtual python isolado no diretório atual (geralmente em `.venv`).

- `source .venv/bin/activate` ativar a venv

- `$ uv pip install -r requirements.txt` - Install Python dependencies 

## Instalação dos requirements

- `uv add django`: Adiciona o pacote Django como dependência do projeto e o instala no ambiente virtual automaticamente.
- `uv list` / `uv pip list`: Lista todos os pacotes e dependências instaladas no ambiente atual.

## Criação do Requirements

- `uv pip freeze > requirements.txt`: Cria o arquivo com todas as dependências necessárias ao projeto agora

## Execução do projeto

- `uv run django-admin startproject <nome> .`: Executa o utilitário do Django para criar a estrutura inicial do projeto no diretório atual. O "." é para não criar uma outra pasta config dentro da pasta config

- `uv run python manage.py startapp <nome>`: Cria a estrutura de um novo aplicativo dentro do projeto Django.

- `uv run python manage.py makemigrations`: Gera os arquivos de migração baseados nas alterações feitas nos modelos do projeto.

- `uv run python manage.py migrate`: Aplica as migrações geradas no banco de dados.

- `uv run python manage.py createsuperuser`: Inicia o prompt para criação de um usuário administrador para acessar o painel administrativo (Admin) do Django.

- `uv run python manage.py runserver`: Inicia o servidor de desenvolvimento local do Django para rodar o projeto.


---

# Resumo de Comandos do Git

## Branches

- `git branch`: Lista todas as branches locais.
- `git branch <nome>`: Cria uma nova branch.
- `git checkout <nome>`: Muda para a branch indicada.
- `git checkout -b <nome>`: Cria e já muda para a nova branch (atalho dos dois acima).
- `git branch -d <nome>`: Deleta uma branch local (só funciona se já foi mergeada).
- `git branch -D <nome>`: Força a deleção de uma branch local.

## Commits e histórico

- `git log --oneline`: Mostra o histórico de commits de forma resumida (hash + mensagem).
- `git status`: Mostra o estado atual dos arquivos (modificados, staged, untracked).
- `git diff`: Mostra as alterações ainda não commitadas.

## Desfazer commits locais (não enviados ao remoto)

- `git reset --soft HEAD~1`: Desfaz o último commit, mas mantém as alterações no stage (prontas para novo commit).
- `git reset --mixed HEAD~1`: Desfaz o último commit e tira as alterações do stage (ficam no working directory).
- `git reset --hard HEAD~1`: Desfaz o último commit e **descarta** as alterações por completo. Use com cuidado!

> Substitua `HEAD~1` por `HEAD~2` para desfazer os 2 últimos commits, e assim por diante.

## Reverter commits já enviados ao remoto (push)

Essa é a forma mais segura quando os commits já foram enviados ao repositório remoto, pois não reescreve o histórico — ela cria um novo commit que desfaz as alterações.

- `git revert HEAD`: Cria um commit que reverte o último commit enviado.
- `git revert HEAD~1..HEAD`: Reverte os 2 últimos commits (cria um commit de reversão para cada um).
- `git revert <hash>`: Reverte um commit específico pelo seu hash (obtido via `git log --oneline`).

Após o revert, envie ao remoto normalmente:
```
git push
```

> **Dica:** Prefira `git revert` ao `git reset` quando os commits já foram enviados ao remoto, para não causar conflitos com outros desenvolvedores.

## Sincronização com o remoto

- `git fetch`: Busca as atualizações do remoto sem aplicar ao branch local.
- `git pull`: Busca e já aplica as atualizações do remoto no branch atual.
- `git push`: Envia os commits locais para o remoto.
- `git push -u origin <nome>`: Envia uma nova branch local para o remoto e configura o tracking.


---

# Como rodar os testes

## Backend (Django)

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

## Frontend (Next.js / Vitest)

```bash
cd react-painel

# Rodar uma vez
npm test

# Watch mode (re-roda ao salvar)
npx vitest
```

Os testes ficam em `react-painel/src/__tests__/components/`.

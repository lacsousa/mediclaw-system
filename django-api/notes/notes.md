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




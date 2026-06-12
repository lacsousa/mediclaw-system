FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /workspaces

# Imagem base ainda traz o repositório apt do Yarn com keyring defasada; o projeto usa pip, não o Yarn do apt.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git \
        libpq-dev \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

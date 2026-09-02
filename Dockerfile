# syntax=docker/dockerfile:1.7
# Multi-stage: as dependencias sao compiladas numa camada descartavel e apenas
# o site-packages resultante vai para a imagem final.
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
# psycopg2-binary traz wheels pre-compilados: nao e preciso gcc/libpq-dev aqui.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.11-slim

# UID/GID fixos: o fsGroup do Pod precisa casar com o GID para que os arquivos
# de secret montados com mode 0440 sejam legiveis. Ver charts/todolist.
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=root:root app.py gunicorn.conf.py ./

# A app le os secrets de arquivos neste diretorio (SECRETS_DIR).
# O diretorio precisa existir mesmo quando nada e montado, senao _config()
# cai no fallback de ambiente sem log.
RUN mkdir -p /var/run/secrets/todolist && chown app:app /var/run/secrets/todolist

USER 10001:10001
EXPOSE 5000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Sem HEALTHCHECK: em Kubernetes quem faz esse papel sao as probes do Pod, e um
# HEALTHCHECK do Docker so gastaria CPU sem ninguem ler o resultado.
ENTRYPOINT ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]

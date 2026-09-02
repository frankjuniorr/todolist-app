# ABOUTME: Configuracao do gunicorn para rodar a todolist em Kubernetes.
# ABOUTME: Um unico worker por Pod, com threads; a escala e horizontal, via HPA.
import os

bind = f"0.0.0.0:{os.environ.get('APP_PORT', '5000')}"

# UM worker, de proposito.
#
# app.py roda `db.create_all()` no import do modulo (app.py:952). Com N workers,
# N processos executam CREATE TABLE contra um banco vazio ao mesmo tempo e o
# perdedor da corrida levanta DuplicateTable -- de forma intermitente, so no
# primeiro deploy, que e o pior tipo de bug para diagnosticar.
#
# A alternativa seria --preload (create_all roda uma vez, no master), mas ai os
# filhos herdam os sockets do pool do SQLAlchemy pelo fork e passam a compartilhar
# conexoes TCP, o que corrompe transacoes. Exigiria um post_fork com
# db.engine.dispose(), ou seja: mais codigo para resolver um problema que a
# escala horizontal ja resolve de graca.
#
# Um worker com threads atende IO-bound (que e o caso: Postgres e API do k8s) e
# deixa o HPA ser o mecanismo de escala -- que e exatamente o que o desafio quer
# ver demonstrado.
workers = 1
threads = int(os.environ.get('GUNICORN_THREADS', '8'))
worker_class = 'gthread'

# get_cleanup_history() faz uma requisicao HTTP sequencial por Pod de Job para
# ler os logs. Com o historico limitado a 10 Pods e timeout de 3s cada, o pior
# caso teorico passa de 30s. 60s da margem sem mascarar um travamento real.
timeout = 60
graceful_timeout = 30

# Mantem a conexao viva entre o Traefik e o Pod.
keepalive = 5

accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
# Sem o header X-Forwarded-For o access log registra o IP do ingress em todas as
# linhas, o que torna o log inutil para depurar acesso.
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s'

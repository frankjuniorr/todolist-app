# todolist-app

Aplicação de exemplo (lista de tarefas), com o empacotamento necessário para rodar em Kubernetes.

O código da aplicação (`app.py`) está **inalterado** em relação ao original. O que foi
adicionado é a camada que faltava para operá-la: imagem, configuração do servidor WSGI,
testes de contrato e pipeline.

| Arquivo | Por que existe |
|---|---|
| `Dockerfile` | Multi-stage, usuário não-root com UID/GID 10001 fixos |
| `gunicorn.conf.py` | Um worker com threads — ver o comentário no arquivo |
| `tests/test_smoke.py` | Trava as suposições que o Helm chart faz sobre a app |
| `.github/workflows/ci.yml` | Lint, teste, build multi-arch, assinatura, SBOM, dispatch |

A infraestrutura que hospeda esta aplicação vive em
[`todolist-platform`](../todolist-platform).

## Rodando localmente

```bash
docker compose up   # ou:
docker build -t todolist:dev .
docker run --rm -p 5000:5000 \
  -e DB_HOST=host.docker.internal -e DB_PASSWORD=todolist \
  todolist:dev
```

## Testes

Exigem um PostgreSQL acessível, porque `app.py` executa `db.create_all()` no import do
módulo — não há como importar o módulo sem banco.

```bash
docker run -d --name pg -p 5432:5432 \
  -e POSTGRES_USER=todolist -e POSTGRES_PASSWORD=todolist -e POSTGRES_DB=todolist \
  postgres:16-alpine
pip install -r requirements.txt -r requirements-dev.txt
DB_PASSWORD=todolist pytest -v tests/
```

## Dois achados no código original

Nenhum dos dois foi corrigido — o objetivo aqui é a plataforma, não a aplicação. Ficam
registrados porque afetam a operação:

1. **`get_cleanup_history()` ordena por string formatada.** `history.sort(key=lambda x: x['started'])`
   opera sobre `'%d/%b %H:%M'`, então `01/Oct` ordena antes de `28/Sep`. O histórico
   embaralha na virada de mês.
2. **Sem `pool_pre_ping` no SQLAlchemy.** Depois de um failover do PostgreSQL, as conexões
   em pool continuam apontando para o primário antigo até estourar o timeout do TCP.
   Mitigado na plataforma pelo `readinessProbe` em `/healthz`, que tira o Pod do Service
   enquanto isso; a correção de verdade seria uma linha em `app.py`.

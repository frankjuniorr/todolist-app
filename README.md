# TodoList

Aplicação web de lista de tarefas.

![Tela principal da aplicação](assets/todolist.png)

## Stack

- Python 3.11
- Flask
- SQLAlchemy
- PostgreSQL
- gunicorn

## Variáveis de ambiente

### Aplicação

| Variável | Padrão | Descrição |
|---|---|---|
| `APP_NAME` | `TodoList` | Título exibido na interface |
| `APP_PORT` | `5000` | Porta do servidor |
| `APP_COLOR` | *(cinza)* | Cor do tema da interface. Valores aceitos abaixo |
| `SESSION_KEY` | `dev-only-insecure-key` | Assina os cookies de sessão via HMAC |
| `ADMIN_USER` | `admin` | Usuário de login |
| `ADMIN_PASSWORD` | `admin` | Senha de login |
| `CLEANUP_TOKEN` | *(vazio)* | Token exigido no header `X-Cleanup-Token` pelo endpoint `POST /cleanup` |

### Banco de dados

| Variável | Padrão | Descrição |
|---|---|---|
| `DB_HOST` | `localhost` | Host do PostgreSQL |
| `DB_PORT` | `5432` | Porta do PostgreSQL |
| `DB_NAME` | `todolist` | Nome do banco |
| `DB_USER` | `todolist` | Usuário do banco |
| `DB_PASSWORD` | *(vazio)* | Senha do usuário do banco |

O schema é criado pela própria aplicação na inicialização. O banco precisa existir e estar
acessível antes de a aplicação subir.

## Credenciais em arquivo

As credenciais podem vir de arquivo, em vez de variável de ambiente. A aplicação procura por
um arquivo com o nome da variável dentro de `SECRETS_DIR`, e usa a variável de ambiente apenas
quando o arquivo não existe.

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRETS_DIR` | `/var/run/secrets/todolist` | Diretório onde a aplicação procura as credenciais em arquivo |

Valores que aceitam arquivo: `DB_USER`, `DB_PASSWORD`, `SESSION_KEY`, `ADMIN_USER`,
`ADMIN_PASSWORD` e `CLEANUP_TOKEN`.

Exemplo: com `SECRETS_DIR` no padrão, um arquivo em
`/var/run/secrets/todolist/DB_PASSWORD` é lido no lugar da variável `DB_PASSWORD`. Espaços e
quebras de linha nas pontas do arquivo são descartados.

## Valores aceitos em `APP_COLOR`

`purple`, `green`, `blue`, `cyan`, `pink`, `red`, `orange`, `brown`, `yellow`.

Valor ausente ou inválido resulta no tema cinza.

## Endpoints

| Endpoint | Método | Autenticação | Descrição |
|---|---|---|---|
| `/` | GET | Sessão | Lista de tarefas |
| `/login` | GET, POST | — | Formulário de login |
| `/logout` | GET | Sessão | Encerra a sessão |
| `/add` | POST | Sessão | Cria uma tarefa |
| `/toggle/<id>` | POST | Sessão | Alterna a tarefa entre feita e pendente |
| `/delete/<id>` | POST | Sessão | Remove uma tarefa |
| `/healthz` | GET | — | Verifica a conexão com o banco e responde `ok` |
| `/cleanup` | POST | Header `X-Cleanup-Token` | Remove todas as tarefas concluídas e responde com a quantidade removida |
| `/pods` | GET | Sessão | Lista os pods do namespace |
| `/cleanup/status` | GET, POST | Sessão | Histórico das execuções de limpeza. O POST suspende ou retoma o agendamento |

## Limpeza das tarefas concluídas

A aplicação não remove tarefas concluídas por conta própria. A limpeza precisa ser acionada de
fora, chamando o endpoint periodicamente com o token no header `X-Cleanup-Token`:

```bash
curl -X POST -H "X-Cleanup-Token: $CLEANUP_TOKEN" http://<host>/cleanup
```

A resposta é a quantidade de tarefas removidas, no formato `deleted N`. Sem o token correto o
endpoint responde `401`.

A página `/cleanup/status` mostra o resultado das últimas execuções e permite pausar e retomar
o agendamento.

## Executando localmente

Requisitos: Python 3.11 e um PostgreSQL acessível.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=todolist
export DB_USER=todolist
export DB_PASSWORD=sua-senha

export SESSION_KEY=chave-local
export ADMIN_USER=admin
export ADMIN_PASSWORD=admin
export CLEANUP_TOKEN=token-local

gunicorn --bind 0.0.0.0:5000 app:app
```

A aplicação fica disponível em `http://localhost:5000`.

## Observações

A aplicação foi escrita para rodar em Kubernetes. Fora de um cluster, parte das
funcionalidades não funciona por completo.

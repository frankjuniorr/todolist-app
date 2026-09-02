# ABOUTME: Prepara o ambiente antes de importar app.py, que roda db.create_all()
# ABOUTME: no import do modulo e portanto exige um Postgres acessivel ja no import.
import os
import pathlib
import tempfile

import pytest

# SECRETS_DIR precisa existir e conter os arquivos ANTES do import de app.py:
# _config() e avaliado em tempo de import (app.py:33-46).
_SECRETS = pathlib.Path(tempfile.mkdtemp(prefix='todolist-secrets-'))
(_SECRETS / 'DB_USER').write_text('todolist\n')
(_SECRETS / 'DB_PASSWORD').write_text(os.environ.get('DB_PASSWORD', 'todolist') + '\n')
(_SECRETS / 'CLEANUP_TOKEN').write_text('token-de-teste\n')
(_SECRETS / 'ADMIN_USER').write_text('admin\n')
(_SECRETS / 'ADMIN_PASSWORD').write_text('admin\n')
(_SECRETS / 'SESSION_KEY').write_text('chave-de-teste\n')

os.environ['SECRETS_DIR'] = str(_SECRETS)
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'todolist')

import app as todolist  # noqa: E402  (o import precisa vir depois do setup acima)


@pytest.fixture()
def client():
    todolist.app.config['TESTING'] = True
    with todolist.app.test_client() as c:
        yield c


@pytest.fixture()
def secrets_dir():
    return _SECRETS


@pytest.fixture()
def mod():
    return todolist

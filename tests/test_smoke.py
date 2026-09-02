# ABOUTME: Testes de contrato entre a aplicacao e a plataforma que a hospeda.
# ABOUTME: Cada teste aqui protege uma suposicao que o Helm chart faz sobre a app.
"""
Estes testes nao existem para validar a logica de negocio da todolist -- ela nao
e nossa. Existem para travar as suposicoes que a plataforma faz sobre a app.
Se um destes quebrar, um manifesto do chart precisa mudar junto.
"""


def test_healthz_ok_com_banco(client):
    """/healthz executa SELECT 1: e o alvo correto do readinessProbe."""
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.data == b'ok'


def test_login_nao_toca_no_banco(client):
    """GET /login renderiza template puro.

    E por isso que ele -- e nao /healthz -- e o alvo do livenessProbe: se o banco
    cair, os Pods saem do Service (readiness) mas nao sao mortos e reiniciados
    (liveness), o que evitaria uma falha em cascata com CrashLoopBackOff.
    """
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'<form' in resp.data


def test_cleanup_sem_token_e_401(client):
    resp = client.post('/cleanup')
    assert resp.status_code == 401


def test_cleanup_responde_exatamente_deleted_n(client):
    """O CronJob de limpeza escreve esta resposta no stdout, e a UI faz
    result.startswith("deleted 0") para decidir a cor do badge em /cleanup/status.
    Qualquer mudanca no formato quebra a tela silenciosamente.
    """
    resp = client.post('/cleanup', headers={'X-Cleanup-Token': 'token-de-teste'})
    assert resp.status_code == 200
    corpo = resp.data.decode()
    assert corpo.startswith('deleted ')
    assert corpo.split()[1].isdigit()


def test_arquivo_tem_precedencia_sobre_variavel_de_ambiente(mod, secrets_dir, monkeypatch):
    """Contrato central: o chart monta secrets como ARQUIVOS, nao como env.

    _config() le o arquivo primeiro e so cai na variavel de ambiente quando o
    arquivo nao existe.
    """
    monkeypatch.setenv('VALOR_DE_TESTE', 'veio-do-ambiente')
    assert mod._config('VALOR_DE_TESTE') == 'veio-do-ambiente'

    (secrets_dir / 'VALOR_DE_TESTE').write_text('  veio-do-arquivo  \n')
    # O valor do arquivo vence, e espacos/quebras nas pontas sao descartados.
    assert mod._config('VALOR_DE_TESTE') == 'veio-do-arquivo'


def test_permissao_negada_cai_no_fallback_silenciosamente(mod, secrets_dir, monkeypatch):
    """Documenta a armadilha mais cara do chart.

    _config() captura OSError e devolve o fallback SEM propagar erro. Um arquivo
    montado com defaultMode incompativel com o fsGroup faz DB_PASSWORD virar
    string vazia, e o sintoma que aparece nos logs e "password authentication
    failed for user" -- que aponta para o Postgres, nao para o volume.

    Por isso o chart usa defaultMode 0440 com fsGroup 10001 casando com o GID
    da imagem.
    """
    alvo = secrets_dir / 'SEGREDO_SEM_PERMISSAO'
    alvo.write_text('valor-secreto\n')
    alvo.chmod(0o000)

    monkeypatch.setenv('SEGREDO_SEM_PERMISSAO', '')
    try:
        # Root ignora bits de permissao; nesse caso o teste nao tem o que provar.
        try:
            alvo.read_text()
            import pytest
            pytest.skip('rodando como root: permissoes de arquivo nao se aplicam')
        except PermissionError:
            pass
        assert mod._config('SEGREDO_SEM_PERMISSAO') == ''
    finally:
        alvo.chmod(0o600)

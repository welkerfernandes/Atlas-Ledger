import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / 'test.db'))) as client:
        client.headers['X-API-Key'] = 'local-alpha'
        yield client

def test_authentication(client):
    client.headers['X-API-Key'] = 'wrong'
    assert client.get('/ledger').status_code == 401

def test_console_and_contract(client):
    assert client.get('/').status_code == 200
    assert 'OPERATIONS' not in client.get('/').text
    assert client.get('/openapi.json').status_code == 200
    assert client.get('/health').json() == {'status': 'ok'}

def setup_accounts(client):
    assert client.post('/accounts', json={'id':'a','opening_balance_cents':10000}).status_code == 201
    assert client.post('/accounts', json={'id':'b','opening_balance_cents':0}).status_code == 201

def command(**changes):
    return {'source':'a','destination':'b','amount_cents':100,'idempotency_key':'one',**changes}

def test_atomic_entries_and_idempotency(client):
    setup_accounts(client)
    first = client.post('/transfers', json=command()).json()
    repeat = client.post('/transfers', json=command()).json()
    assert repeat['id'] == first['id'] and repeat['replayed']
    assert client.post('/transfers', json=command(amount_cents=101)).status_code == 409
    state = client.get('/ledger').json()
    assert state['balanced'] and len(state['outbox']) == 1
    assert [a['balance'] for a in state['accounts']] == [9900,100]

def test_insufficient_funds_rolls_back(client):
    setup_accounts(client)
    assert client.post('/transfers', json=command(amount_cents=10001)).status_code == 409
    assert client.get('/ledger').json()['outbox'] == []
    assert client.get('/ledger').json()['accounts'][0]['balance'] == 10000

def test_tenant_isolation(client):
    setup_accounts(client)
    client.headers['X-API-Key'] = 'local-beta'
    assert client.get('/ledger').json()['accounts'] == []
    assert client.post('/transfers', json=command()).status_code == 404

@pytest.mark.parametrize('changes', [{'amount_cents':0},{'amount_cents':-1},{'amount_cents':1.5},{'destination':'a'}])
def test_invalid_commands(client, changes):
    assert client.post('/transfers', json=command(**changes)).status_code == 422

def test_robust_anomaly():
    from app.domain import anomaly
    assert anomaly(100, [100]*5)['status'] == 'normal'
    assert anomaly(10000, [100]*5)['status'] == 'review'
    assert anomaly(100, [])['status'] == 'insufficient_history'

def test_concurrent_retries(client):
    from concurrent.futures import ThreadPoolExecutor
    setup_accounts(client)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: client.post('/transfers', json=command()), range(16)))
    assert all(r.status_code == 200 for r in results)
    assert len({r.json()['id'] for r in results}) == 1
    assert len(client.get('/ledger').json()['outbox']) == 1

def test_concurrent_spending_cannot_overdraw(client):
    from concurrent.futures import ThreadPoolExecutor
    setup_accounts(client)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda n: client.post('/transfers', json=command(amount_cents=3000,idempotency_key=str(n))), range(8)))
    assert sum(r.status_code == 200 for r in results) == 3
    state = client.get('/ledger').json()
    assert state['accounts'][0]['balance'] == 1000 and state['balanced']

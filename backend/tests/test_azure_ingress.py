import pytest
from fastapi.testclient import TestClient
from app import main, security


def configure(monkeypatch):
    monkeypatch.setenv('MATCHOS_ENV','production')
    monkeypatch.setenv('MATCHOS_PROXY_MODE','azure-container-apps')
    monkeypatch.setenv('CONTAINER_APP_NAME','matchos-test')
    monkeypatch.setenv('CONTAINER_APP_ENV_DNS_SUFFIX','test.canadacentral.azurecontainerapps.io')


def test_forwarded_headers_remain_untrusted_by_default(monkeypatch):
    monkeypatch.setenv('MATCHOS_ENV','production')
    monkeypatch.setenv('MATCHOS_PROXY_MODE','none')
    with TestClient(main.app) as client:
        r=client.get('/api/health',headers={'x-forwarded-proto':'https','x-forwarded-for':'203.0.113.8'})
    assert r.status_code==400


def test_managed_ingress_uses_only_rightmost_ip_and_preserves_secure_session(monkeypatch):
    configure(monkeypatch)
    with TestClient(main.app,headers={'x-forwarded-proto':'https','x-forwarded-for':'1.2.3.4, 203.0.113.8','x-matchos-client':'replay'}) as client:
        r=client.post('/api/session',json={})
        assert r.status_code==200
        cookie=r.headers['set-cookie'].lower()
        assert 'secure' in cookie and 'httponly' in cookie and 'samesite=strict' in cookie
        assert r.headers['strict-transport-security']
        assert client.get('/docs').status_code==404
        assert client.get('/api/health',headers={'host':'attacker.example'}).status_code==400
    assert ('client','203.0.113.8') in security.rates
    assert ('client','1.2.3.4') not in security.rates


@pytest.mark.parametrize('headers',[
    {}, {'x-forwarded-proto':'https'},
    {'x-forwarded-proto':'https,http','x-forwarded-for':'203.0.113.8'},
    {'x-forwarded-proto':'https','x-forwarded-for':'invalid'},
    {'x-forwarded-proto':'http','x-forwarded-for':'203.0.113.8'},
])
def test_missing_malformed_or_insecure_managed_headers_fail_closed(monkeypatch,headers):
    configure(monkeypatch)
    with TestClient(main.app) as client:
        assert client.get('/api/health',headers=headers).status_code==400


def test_platform_mode_cannot_be_enabled_accidentally_on_another_host(monkeypatch):
    configure(monkeypatch)
    monkeypatch.delenv('CONTAINER_APP_NAME')
    with TestClient(main.app) as client:
        assert client.get('/api/health',headers={'x-forwarded-proto':'https','x-forwarded-for':'203.0.113.8'}).status_code==400

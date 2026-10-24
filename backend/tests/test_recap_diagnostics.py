import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from app import main,recap_diagnostics,recap_quality
from app.models import CatchUpRequest


def test_trace_is_opt_in_bounded_nested_and_request_scoped():
    recap_diagnostics.record('outside',draft={'en':'not retained'})
    with recap_diagnostics.capture() as outer:
        recap_diagnostics.record('draft',draft={'en':'x'*10000,'es':'texto','fact_ids':['f'], 'api-key':'never-copy'})
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(recap_diagnostics.record,'unrelated_request',draft={'en':'private'}).result()
        with recap_diagnostics.capture() as inner:
            recap_diagnostics.record('nested',error=recap_quality.RecapQualityError('wrong_clock',expected='55:00'))
        for _ in range(12): recap_diagnostics.record('bounded')
    assert len(outer)==8 and len(inner)==1
    assert len(outer[0]['draft']['en'])==9000
    assert 'never-copy' not in json.dumps(outer) and 'unrelated_request' not in json.dumps(outer)
    with recap_diagnostics.capture() as fresh:
        assert fresh==[]


def test_local_audit_uses_owned_replay_and_normal_fan_route_never_exposes_draft(monkeypatch):
    def build(*args):
        recap_diagnostics.record('draft',draft={'en':'Rejected private draft','es':'Borrador rechazado','fact_ids':[]})
        return {'fan_briefing':{'spoken_recap':{'en':'Safe summary','es':'Resumen verificado'}}}
    monkeypatch.setattr(main,'build_catch_up',build)
    with TestClient(main.app,client=('127.0.0.1',50000),headers={'X-MatchOS-Client':'replay'}) as owner:
        owner.post('/api/session',json={}).raise_for_status()
        owner.post('/api/matchdays/start',json={'matchday_id':'trace-day'}).raise_for_status()
        audit=owner.post('/api/development/matches/trace-day-featured/catch-up',json={})
        assert audit.status_code==200
        assert audit.json()['evaluation_trace'][0]['draft']['en']=='Rejected private draft'
        normal=owner.post('/api/matches/trace-day-featured/catch-up',json={})
        assert normal.status_code==200 and 'Rejected private draft' not in normal.text
        assert 'evaluation_trace' not in normal.json()
        with TestClient(main.app,client=('127.0.0.1',50001),headers={'X-MatchOS-Client':'replay'}) as other:
            other.post('/api/session',json={}).raise_for_status()
            assert other.post('/api/development/matches/trace-day-featured/catch-up',json={}).status_code==403


def test_audit_endpoint_is_hidden_from_remote_clients_and_production(monkeypatch):
    with TestClient(main.app,client=('198.51.100.7',50000),headers={'X-MatchOS-Client':'replay'}) as remote:
        assert remote.post('/api/development/matches/anything/catch-up',json={}).status_code==404
    monkeypatch.setattr(main.security,'production',lambda:True)
    request=Request({'type':'http','method':'POST','path':'/','headers':[], 'client':('127.0.0.1',50000)})
    with pytest.raises(HTTPException) as error:
        main.audit_catch_up('anything',request,CatchUpRequest())
    assert error.value.status_code==404

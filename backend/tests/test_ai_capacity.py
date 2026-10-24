import json
from datetime import datetime, timezone
import httpx
import pytest
from fastapi.testclient import TestClient
from app import ai_capacity, main, security, story_writer
from app.explanations import explain
from test_explanations import STORIES
from test_story_writer import configured, inputs, DRAFT, REVIEW

ENDPOINT='https://fixture.openai.azure.com/openai/v1'
MODEL='matchos-explainer'


@pytest.mark.parametrize('headers,expected', [
    ({'retry-after-ms':'2500'},3), ({'retry-after':'120'},120),
    ({'retry-after-ms':'1000','retry-after':'60'},60),
    ({'retry-after':'86400'},86400), ({},60),
    ({'retry-after':'NaN','retry-after-ms':'broken'},60),
    ({'retry-after':'-5'},60), ({'retry-after':'0'},1),
])
def test_provider_wait_headers_are_honored_without_sleeping_or_unbounded_state(monkeypatch,headers,expected):
    monkeypatch.setattr(ai_capacity.time,'monotonic',lambda:100)
    assert ai_capacity.record_limit(ENDPOINT,MODEL,httpx.Headers(headers))==expected
    assert ai_capacity.remaining(ENDPOINT+'/',MODEL)==expected
    assert ai_capacity.remaining(ENDPOINT,'other-model')==0
    monkeypatch.setattr(ai_capacity.time,'monotonic',lambda:100+expected)
    assert ai_capacity.remaining(ENDPOINT,MODEL)==0
    assert not ai_capacity.COOLDOWNS


def test_longer_active_wait_is_never_shortened_and_map_is_bounded(monkeypatch):
    monkeypatch.setattr(ai_capacity.time,'monotonic',lambda:100)
    ai_capacity.record_limit(ENDPOINT,MODEL,{'retry-after':'120'})
    ai_capacity.record_limit(ENDPOINT,MODEL,{'retry-after':'1'})
    assert ai_capacity.remaining(ENDPOINT,MODEL)==120
    for n in range(20):ai_capacity.record_limit(ENDPOINT,str(n),{})
    assert len(ai_capacity.COOLDOWNS)==8


def test_http_date_retry_header_is_honored(monkeypatch):
    class FixedDate:
        @staticmethod
        def now(tz):return datetime(2026,10,24,12,0,0,tzinfo=timezone.utc)
    monkeypatch.setattr(ai_capacity,'datetime',FixedDate)
    assert ai_capacity.record_limit(ENDPOINT,MODEL,{'retry-after':'Sat, 24 Oct 2026 12:00:30 GMT'})==30


def test_selector_limit_stops_writer_and_both_resume_after_the_wait(configured,monkeypatch):
    clock=[100.0]
    monkeypatch.setattr(ai_capacity.time,'monotonic',lambda:clock[0])
    requests=[]
    def limited(request):
        requests.append(request)
        return httpx.Response(429,headers={'retry-after-ms':'65000'},text='private-provider-body')
    with httpx.Client(transport=httpx.MockTransport(limited)) as client:
        selection=explain(STORIES,'casual',client)
        assert selection['fallback_reason']=='provider_http_429'
        result=story_writer.write(*inputs(),client)
        again=explain(STORIES,'casual',client)
    assert result['fallback_reason']==again['fallback_reason']=='provider_cooldown'
    assert result['retry_after_seconds']==65 and len(requests)==1
    assert security.ai_calls==2 and security.ai_active==0
    assert 'private-provider-body' not in json.dumps(result)
    clock[0]=166
    def success(request):
        body=json.loads(request.content)
        requests.append(request)
        value=DRAFT if body['response_format']['json_schema']['name']=='match_recap' else REVIEW
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(value)}}]})
    with httpx.Client(transport=httpx.MockTransport(success)) as client:
        written=story_writer.write(*inputs(),client)
    assert written['mode']=='azure' and len(requests)==3 and security.ai_active==0


def test_writer_limit_stops_the_selector_too(configured):
    calls=[]
    def limited(request):
        calls.append(request)
        return httpx.Response(429,headers={'retry-after':'30'})
    with httpx.Client(transport=httpx.MockTransport(limited)) as client:
        first=story_writer.write(*inputs(),client)
        other=explain(STORIES,'advanced',client)
    assert first['fallback_reason']=='provider_http_429' and first['retry_after_seconds']==30
    assert other['fallback_reason']=='provider_cooldown' and len(calls)==1


@pytest.mark.parametrize('reason',['provider_http_429','provider_cooldown'])
def test_rate_limited_snapshot_is_not_cached_forever(monkeypatch,reason):
    results=[]
    def build(*args):
        results.append(1)
        return {'fan_briefing':{'narrative':{'mode':'deterministic' if len(results)==1 else 'azure',
                                         'fallback_reason':reason if len(results)==1 else None}}}
    monkeypatch.setattr(main,'build_catch_up',build)
    with TestClient(main.app,headers={'X-MatchOS-Client':'replay'}) as client:
        for _ in range(3):
            client.post('/api/matches/capacity-test/catch-up',json={}).raise_for_status()
    assert len(results)==2  # First failure is retryable; reviewed success is cached.

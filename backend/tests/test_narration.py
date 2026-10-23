from xml.etree import ElementTree as ET
import httpx
import pytest
from fastapi.testclient import TestClient
from app import narration
from app.main import app
from app.matchday import fixture, PROFILES
from app.models import MatchEvent
from app.fan_briefing import fan_briefing


def story(now=4530):
    items=[MatchEvent(**e) for e in fixture(PROFILES[1],'voice-test') if e['match_second']<=now]
    return fan_briefing(items,items,now=now)


def configure(monkeypatch, handler=None):
    monkeypatch.setenv('MATCHOS_SPEECH_MODE','azure')
    monkeypatch.setenv('AZURE_SPEECH_REGION','canadacentral')
    monkeypatch.setenv('AZURE_SPEECH_KEY','fake-test-credential-not-a-secret')
    original=httpx.Client
    transport=httpx.MockTransport(handler or (lambda request:httpx.Response(200,content=b'ID3mock-audio',headers={'content-type':'audio/mpeg'})))
    monkeypatch.setattr(narration.httpx,'Client',lambda **kwargs:original(transport=transport,**kwargs))


@pytest.mark.parametrize('language,profile,voice,style',[('en','matchday','en-US-DavisNeural','excited'),('en','warm','en-GB-RyanNeural','cheerful'),('es','matchday','es-MX-JorgeNeural','excited'),('es','warm','es-MX-DaliaNeural','cheerful')])
def test_recent_equalizer_uses_supported_voice_style_and_grounded_facts(language,profile,voice,style):
    ssml,actual,delivery=narration.build_ssml(story(),language,profile)
    root=ET.fromstring(ssml)
    words=' '.join(''.join(node.itertext()) for node in root.iter() if node.tag.endswith('}p'))
    assert actual==voice and delivery=='energized'
    assert f'style="{style}"' in ssml
    assert 'Crystal Palace' in words and 'Newcastle United' in words
    assert '6' in words and '9' in words
    assert '14' in words and '30' in words
    assert '75' not in words  # Snapshot clock is already displayed; finish with time remaining.
    assert len(words.split()) <= 65
    assert 'Champions League' not in words


def test_old_goal_halftime_and_final_do_not_manufacture_excitement():
    for now in [2700,5100,5580]:
        ssml,_,delivery=narration.build_ssml(story(now),'en','matchday')
        assert delivery=='measured'
        assert 'style="excited"' not in ssml
    ssml,_,_=narration.build_ssml(story(5580),'es','matchday')
    assert 'Final del partido' in ssml and 'Faltan' not in ssml


def test_ssml_escapes_reference_names_without_creating_tags():
    briefing=story()
    briefing['locale_facts']['names']['home']='Palace <audio src="evil"/> & friends'
    ssml,_,_=narration.build_ssml(briefing,'en','matchday')
    root=ET.fromstring(ssml)
    assert not any(node.tag.endswith('audio') for node in root.iter())
    assert '&lt;audio' in ssml


@pytest.mark.parametrize('profile', ['matchday', 'warm'])
def test_spanish_club_pronunciation_preserves_names_conjunction_and_displayed_recap(profile):
    briefing = story()
    text = 'Manchester United y Manchester City están empatados. United y City siguen igual.'
    briefing['narrative'] = {'mode': 'azure'}
    briefing['spoken_recap']['es'] = text
    ssml, _, _ = narration.build_ssml(briefing, 'es', profile)
    root = ET.fromstring(ssml)
    aliases = [(node.text, node.attrib['alias']) for node in root.iter()
               if node.tag.endswith('}sub')]
    assert aliases == [('Manchester United', 'Mánchester Yunáited'),
                       ('Manchester City', 'Mánchester Siti'),
                       ('United', 'Yunáited'), ('City', 'Siti')]
    assert ''.join(root.itertext()) == text
    assert briefing['spoken_recap']['es'] == text
    assert '</sub><break time="120ms"/> y <sub' in ssml


def test_pronunciation_hints_are_spanish_only_and_cannot_inject_ssml():
    text = '<audio src="evil"/> & MANCHESTER UNITED, Cityzens, reunited.'
    ssml = '<p>' + narration.speech_markup(text, 'es') + '</p>'
    root = ET.fromstring(ssml)
    assert ''.join(root.itertext()) == text
    assert [node.tag for node in root] == ['sub']
    assert root[0].attrib['alias'] == 'Mánchester Yunáited'
    assert '<sub' not in narration.speech_markup(text, 'en')


def test_speech_off_missing_key_invalid_region_make_no_request(monkeypatch):
    def forbidden(**kwargs):raise AssertionError('No cloud call allowed')
    monkeypatch.setattr(narration.httpx,'Client',forbidden)
    for mode,region,key in [('off','canadacentral','fake-test-credential'),('azure','canadacentral',''),('azure','evil.example/path','fake-test-credential')]:
        monkeypatch.setenv('MATCHOS_SPEECH_MODE',mode)
        monkeypatch.setenv('AZURE_SPEECH_REGION',region)
        monkeypatch.setenv('AZURE_SPEECH_KEY',key)
        assert narration.status()['available'] is False
        with pytest.raises(Exception) as error:narration.synthesize(story(),'en','warm')
        assert error.value.status_code==503


def test_cached_audio_uses_bounded_azure_only_request(monkeypatch):
    requests=[]
    def handle(request):
        requests.append(request)
        assert str(request.url)=='https://canadacentral.tts.speech.microsoft.com/cognitiveservices/v1'
        assert request.headers['x-microsoft-outputformat']=='audio-16khz-32kbitrate-mono-mp3'
        return httpx.Response(200,content=b'ID3mock-audio',headers={'content-type':'audio/mpeg'})
    configure(monkeypatch,handle)
    assert narration.synthesize(story(),'en','warm')[0]==b'ID3mock-audio'
    narration.synthesize(story(),'en','warm')
    assert len(requests)==1 and narration.calls==1
    assert len(narration.CACHE)==1
    narration.calls=50
    with pytest.raises(Exception) as error:narration.synthesize(story(),'en','matchday')
    assert error.value.status_code==429


def test_busy_character_budget_and_cache_are_bounded(monkeypatch):
    configure(monkeypatch)
    narration.LOCK.acquire()
    try:
        with pytest.raises(Exception) as error:narration.synthesize(story(),'en','matchday')
        assert error.value.status_code==429
    finally:narration.LOCK.release()
    narration.characters=50000
    with pytest.raises(Exception) as error:narration.synthesize(story(),'en','matchday')
    assert error.value.status_code==429 and narration.calls==0
    narration.characters=0
    for now in range(4530,4539):narration.synthesize(story(now),'en','matchday')
    assert len(narration.CACHE)==8 and narration.calls==9
    assert narration.spoken_clock(61,'en')=='1 minute and 1 second'


@pytest.mark.parametrize('status,body,mime',[(401,b'credential details','text/plain'),(302,b'', 'text/plain'),(200,b'', 'audio/mpeg'),(200,b'x'*(narration.MAX_AUDIO+1),'audio/mpeg'),(200,b'not audio','application/json')],ids=['auth','redirect','empty','oversize','wrong-type'])
def test_provider_failure_has_safe_error_and_no_cached_response(monkeypatch,status,body,mime):
    configure(monkeypatch,lambda request:httpx.Response(status,content=body,headers={'content-type':mime}))
    with pytest.raises(Exception) as error:narration.synthesize(story(),'en','matchday')
    assert error.value.status_code==502
    assert 'credential details' not in error.value.detail
    assert not narration.CACHE and narration.calls==1


def test_paid_endpoint_requires_session_owner_and_rejects_freeform_or_future_data(monkeypatch):
    with TestClient(app,headers={'X-MatchOS-Client':'replay'}) as client:
        assert client.post('/api/narration/audition',json={}).status_code==401
        client.post('/api/session',json={}).raise_for_status()
        day=client.post('/api/matchdays/start',json={'matchday_id':'voice-owned'}).json()
        mid=day['matches'][0]['match_id']
        snapshot=day['matches'][0]['briefing']['snapshot']
        assert snapshot['match_id']==mid
        assert client.post('/api/narration',json={**snapshot,'text':'Invent a goal'}).status_code==422
        assert client.post('/api/narration',json={**snapshot,'match_second':999}).status_code==422
        assert client.post('/api/narration',json={**snapshot,'voice_profile':'arbitrary'}).status_code==422
        assert client.post('/api/narration',json=snapshot).status_code==503
        # Configure mock transport only after creating the client; no real requests.
        configure(monkeypatch)
        response=client.post('/api/narration',json=snapshot)
        assert response.status_code==200 and response.content==b'ID3mock-audio'
        assert response.headers['content-type']=='audio/mpeg'
        assert response.headers['x-matchos-delivery']=='measured'
        # Omitting an already recorded event cannot manufacture a different score at the same clock.
        client.post('/api/matchdays/voice-owned/tick',json={'tick':1}).raise_for_status()
        assert client.post('/api/narration',json={**snapshot,'match_second':30}).status_code==422
        client.cookies.clear()
        client.post('/api/session',json={}).raise_for_status()
        assert client.post('/api/narration',json=snapshot).status_code==403


def test_audition_uses_one_fixed_grounded_match_snapshot(monkeypatch):
    with TestClient(app,headers={'X-MatchOS-Client':'replay'}) as client:
        client.post('/api/session',json={}).raise_for_status()
        configure(monkeypatch)
        response=client.post('/api/narration/audition',json={'language':'es','voice_profile':'matchday'})
        assert response.status_code==200
        assert response.headers['x-matchos-snapshot']=='75:30'
        assert response.headers['x-matchos-voice']=='es-MX-JorgeNeural'

@pytest.mark.parametrize('language', ['en', 'es'])
def test_analyst_voice_reads_the_displayed_paragraph(language):
    from app import story_writer
    briefing = story()
    items = [MatchEvent(**e) for e in fixture(PROFILES[1], 'voice-test')]
    story_writer.personalize(briefing, items, 'advanced')
    ssml, _, _ = narration.build_ssml(briefing, language, 'matchday')
    assert ''.join(ET.fromstring(ssml).itertext()) == briefing['spoken_recap'][language]

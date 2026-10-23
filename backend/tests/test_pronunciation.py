from xml.etree import ElementTree as ET
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app, audition_voice, VoiceAuditionRequest
from app import narration
from app.pronunciation import DATA, ROSTER_NAMES, audition_names, speech_markup


@pytest.mark.parametrize('language,connector', [('en', 'and'), ('es', 'y')])
def test_every_roster_name_survives_ssml_with_conjunctions_and_punctuation(language, connector):
    text = '; '.join(f'{name} {connector} {name}.' for name in ROSTER_NAMES)
    root = ET.fromstring('<p>' + speech_markup(text, language) + '</p>')
    assert ''.join(root.itertext()) == text
    assert all(entry['name'] in ROSTER_NAMES for entry in DATA['players'])
    assert all(entry['source'] in DATA['sources'] for entry in DATA['players'])


def test_full_names_win_over_short_forms_and_spanish_surnames_do_not_collide():
    text = 'Bruno Fernandes y Enzo Fernandez; Mateo Kovačić, Joško Gvardiol, Mainoo.'
    root = ET.fromstring('<p>' + speech_markup(text, 'es') + '</p>')
    assert ''.join(root.itertext()) == text
    assert [node.text for node in root] == ['Bruno Fernandes', 'Enzo Fernandez', 'Mateo Kovačić',
                                          'Joško Gvardiol', 'Mainoo']
    assert root[0].attrib['alias'] == 'Bruno Fernánsh'
    assert root[1].attrib['alias'] == 'Enzo Fernández'
    assert '<sub' not in speech_markup(text, 'en')
    assert '<sub' not in speech_markup('Cityzens reunited. Mainoos and Mbeumology.', 'es')


def test_roster_batches_cover_every_player_once_without_freeform_input():
    names = tuple(name for batch in range(21) for name in audition_names(batch))
    assert names == ROSTER_NAMES
    assert audition_names(-1) == ()
    assert audition_names(20) == ()


@pytest.mark.parametrize('profile', ['matchday', 'warm'])
def test_reported_spanish_names_get_hints_in_actual_recap_context(profile):
    text = ('Crystal Palace y Newcastle United están empatados 1 a 1. '
            'Harvey Barnes marcó para Newcastle United a los 15:11. '
            'Ismaila Sarr marcó para Crystal Palace a los 60:11. '
            'A los 60:10, Crystal Palace registró un remate 10 segundos después de recuperar '
            'el balón en la misma posesión. En los últimos cinco minutos se registró 1 remate, '
            'frente a 0 en los cinco anteriores. Faltan 27 minutos y 30 segundos para los noventa, más el añadido.')
    ssml, _, _ = narration.build_ssml({'audience':'advanced','spoken_recap':{'es':text}}, 'es', profile)
    root = ET.fromstring(ssml)
    assert ''.join(root.itertext()) == text
    aliases = {node.text:node.attrib['alias'] for node in root.iter() if node.tag.endswith('}sub')}
    assert aliases['Harvey Barnes'] == 'Járvi Barns'
    assert aliases['Ismaila Sarr'] == 'Ismaíla Sar'
    assert '15:11' in ssml and '60:11' in ssml  # User identified the names, not a timing error.


def test_reported_names_handle_short_forms_accents_and_english_separately():
    text = 'Ismaïla Sarr y Harvey Barnes. Sarr encontró a Barnes; Ismaila y Harvey.'
    root = ET.fromstring('<p>' + speech_markup(text, 'es') + '</p>')
    assert ''.join(root.itertext()) == text
    assert [node.attrib['alias'] for node in root] == ['Ismaíla Sar', 'Járvi Barns', 'Sar', 'Barns', 'Ismaíla', 'Járvi']
    assert '<sub' not in speech_markup(text, 'en')
    assert '<sub' not in speech_markup('Barnesville, Sarrs, Harveyson.', 'es')


@pytest.mark.parametrize('text', [
    'Crystal Palace y Newcastle United están empatados 1 a 1.',
    'Manchester United y Manchester City están empatados.',
    'Newcastle United y Crystal Palace están empatados.',
    'Brighton y Fulham siguen empatados.',
    'United y City.',
])
def test_two_team_names_get_one_short_boundary_without_changing_sentence(text):
    root = ET.fromstring('<p>' + speech_markup(text, 'es') + '</p>')
    assert ''.join(root.itertext()) == text
    assert [node.attrib for node in root if node.tag == 'break'] == [{'time':'120ms'}]
    assert '<break' not in speech_markup(text, 'en')


def test_pauses_cover_all_known_team_pairs_and_do_not_break_player_names():
    from app.pronunciation import TEAM_NAMES
    for home in TEAM_NAMES:
        for away in TEAM_NAMES:
            if home == away:
                continue
            text = f'{home} y {away}.'
            root = ET.fromstring('<p>' + speech_markup(text, 'es') + '</p>')
            assert ''.join(root.itertext()) == text
            assert len(root.findall('break')) == 1
    assert '<break' not in speech_markup('Harvey Barnes y Ismaila Sarr.', 'es')


@pytest.mark.parametrize('profile', ['matchday', 'warm'])
@pytest.mark.parametrize('language', ['en', 'es'])
def test_all_four_voices_preserve_every_roster_batch(language, profile):
    for batch in range(12):
        text = '. '.join(audition_names(batch)) + '.'
        ssml, voice, _ = narration.build_ssml({'audience': 'advanced',
                                              'spoken_recap': {language: text}}, language, profile)
        root = ET.fromstring(ssml)
        assert ''.join(root.itertext()) == text
        assert voice == narration.PROFILES[profile][language][0]
        assert root.attrib['{http://www.w3.org/XML/1998/namespace}lang'].startswith(language + '-')
        if language == 'en':
            assert '<sub' not in ssml


def test_roster_audition_requires_session_is_bounded_and_rejects_text(monkeypatch):
    calls = []
    monkeypatch.setattr(narration, 'synthesize', lambda briefing, language, profile:
                        (calls.append((briefing, language, profile)) or
                         (b'ID3test', 'es-MX-JorgeNeural', 'measured')))
    with TestClient(app, headers={'X-MatchOS-Client': 'replay'}) as client:
        path = '/api/narration/audition'
        assert client.post(path, json={'roster_batch': 0}).status_code == 401
        client.post('/api/session', json={}).raise_for_status()
        assert client.post(path, json={'roster_batch': 0, 'text': 'Invent something'}).status_code == 422
        assert client.post(path, json={'roster_batch': 20}).status_code == 422
        response = client.post(path, json={'roster_batch': 0, 'language': 'es'})
        assert response.status_code == 200
        assert response.headers['x-matchos-snapshot'] == 'Roster audition'
        assert calls[0][0]['spoken_recap']['es'] == '. '.join(audition_names(0)) + '.'
        monkeypatch.setattr('app.security.production', lambda: True)
        with pytest.raises(HTTPException) as error:
            audition_voice(VoiceAuditionRequest(roster_batch=0), None)
        assert error.value.status_code == 404

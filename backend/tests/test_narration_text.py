from xml.etree import ElementTree as ET
import pytest
from app.fan_briefing import fan_briefing
from app.narration import build_ssml
from app.narration_text import recap_text
from test_fan_briefing import event
from test_narration import story


@pytest.mark.parametrize('teams,en,es', [
    (['home'], 'Palace took the lead.', 'Palace se adelantó.'),
    (['home', 'home'], 'Palace extended their lead.', 'Palace amplió su ventaja.'),
    (['away', 'away', 'home'], 'Palace pulled a goal back.', 'Palace recortó la diferencia.'),
    (['away', 'home'], 'Palace pulled level.', 'Palace empató.'),
    (['away', 'home', 'home'], 'Palace turned it around to lead.', 'Palace remontó para ponerse por delante.'),
])
@pytest.mark.parametrize('language', ['en', 'es'])
def test_turning_points_keep_distinct_meanings_and_exact_scores(teams, en, es, language):
    goals = [event(i+2, 100+i*60, 'goal', team) for i, team in enumerate(teams)]
    briefing = fan_briefing([event(1, 0, 'kickoff', 'away')]+goals, [goals[-1]])
    text = recap_text(briefing, language)
    assert text.startswith(es if language == 'es' else en)
    expected_scores = {
        (1, 0): ('Palace lead Newcastle 1 to 0.', 'Palace va por delante de Newcastle, 1 a 0.'),
        (2, 0): ('Palace lead Newcastle 2 to 0.', 'Palace va por delante de Newcastle, 2 a 0.'),
        (1, 2): ('Newcastle lead Palace 2 to 1.', 'Newcastle va por delante de Palace, 2 a 1.'),
        (1, 1): ('Palace and Newcastle are level at 1 all.', 'Palace y Newcastle están empatados 1 a 1.'),
        (2, 1): ('Palace lead Newcastle 2 to 1.', 'Palace va por delante de Newcastle, 2 a 1.'),
    }
    assert expected_scores[(teams.count('home'), teams.count('away'))][language == 'es'] in text
    assert len(briefing['trajectory']['evidence_event_ids']) == len(goals)


@pytest.mark.parametrize('language', ['en', 'es'])
def test_device_and_cloud_share_the_same_concise_story_without_changing_evidence(language):
    briefing = story()
    text = briefing['spoken_recap'][language]
    ssml, _, _ = build_ssml(briefing, language, 'matchday')
    spoken = ' '.join(''.join(node.itertext()) for node in ET.fromstring(ssml).iter()
                      if node.tag.endswith('}p'))
    assert spoken == text == recap_text(briefing, language)
    assert len(text.split()) <= 65
    assert len(briefing['trajectory']['transitions']) == 4
    assert len(briefing['trajectory']['evidence_event_ids']) == 4
    assert '3' in briefing['sections'][1]['text']  # Detailed per-team shots stay in drawer.
    assert ('twice' if language == 'en' else 'dos veces') in text


@pytest.mark.parametrize('language', ['en', 'es'])
def test_quiet_increment_does_not_announce_or_energize_an_already_seen_goal(language):
    events = [event(1, 0, 'kickoff'), event(2, 100, 'goal'), event(3, 120, 'pass')]
    briefing = fan_briefing(events, [events[-1]], now=120)
    ssml, _, delivery = build_ssml(briefing, language, 'matchday')
    assert delivery == 'measured' and 'style="excited"' not in ssml
    text = recap_text(briefing, language)
    assert ('No new goals' if language == 'en' else 'No hay nuevos goles') in text
    assert 'took the lead' not in text and 'se adelantó' not in text


@pytest.mark.parametrize('language', ['en', 'es'])
def test_quiet_window_does_not_claim_pressure_and_comparison_requires_coverage(language):
    quiet = [event(1, 0, 'kickoff'), event(2, 600, 'pass')]
    text = recap_text(fan_briefing(quiet, quiet), language)
    assert ('Still goalless' if language == 'en' else 'Sigue sin goles') in text
    assert ('No shots recorded' if language == 'en' else 'Sin remates registrados') in text
    # Two recent shots, no history covering the preceding window.
    short = [event(1, 580, 'shot'), event(2, 600, 'shot', 'away')]
    briefing = fan_briefing(short, short)
    text = recap_text(briefing, language)
    assert 'up from' not in text and 'frente a' not in text
    assert 'pressure' not in text and 'presión' not in text


@pytest.mark.parametrize('language', ['en', 'es'])
def test_observed_shot_increase_is_described_without_predicting_a_goal(language):
    events = [event(1, 0, 'kickoff'), event(2, 100, 'shot'),
              event(3, 500, 'shot'), event(4, 600, 'shot', 'away')]
    text = recap_text(fan_briefing(events, events), language)
    assert ('up from 1' if language == 'en' else 'frente a 1') in text
    assert 'next goal' not in text and 'próximo gol' not in text


@pytest.mark.parametrize('kind,second,en,es', [
    ('half_end', 2700, 'Half-time.', 'Descanso.'),
    ('match_end', 5580, 'Full-time.', 'Final del partido.'),
])
@pytest.mark.parametrize('language', ['en', 'es'])
def test_break_and_final_are_retrospective_without_live_clock_or_shot_window(kind, second, en, es, language):
    events = [event(1, 0, 'kickoff', 'away'), event(2, 100, 'goal'), event(3, second, kind)]
    briefing = fan_briefing(events, [events[-1]])
    text = recap_text(briefing, language)
    assert text.startswith(es if language == 'es' else en)
    expected = {
        ('en', 'half_end'): 'Palace lead Newcastle 1 to 0.',
        ('en', 'match_end'): 'Palace beat Newcastle 1 to 0.',
        ('es', 'half_end'): 'Palace va por delante de Newcastle, 1 a 0.',
        ('es', 'match_end'): 'Palace ganó 1 a 0 a Newcastle.',
    }
    assert expected[(language, kind)] in text
    assert not any(word in text for word in ('until ninety', 'Faltan', 'last five', 'últimos cinco'))
    assert build_ssml(briefing, language, 'matchday')[2] == 'measured'


def test_energy_cutoff_added_time_and_future_events():
    events = [event(1, 0, 'kickoff'), event(2, 100, 'goal')]
    for now, expected in [(280, 'energized'), (281, 'measured')]:
        briefing = fan_briefing(events, events, now=now)
        assert build_ssml(briefing, 'en', 'matchday')[2] == expected
    for now in (5400, 5401):
        briefing = fan_briefing(events, events, now=now)
        assert 'Added time is being played.' in recap_text(briefing, 'en')
        assert 'Faltan' not in recap_text(briefing, 'es')
    future = event(3, 601, 'goal', 'away')
    briefing = fan_briefing(events+[future], [events[0], future], now=60)
    assert not briefing['locale_facts']['has_new_goals']
    assert briefing['trajectory']['score'] == {'home': 0, 'away': 0}
    assert 'Still goalless.' in recap_text(briefing, 'en')

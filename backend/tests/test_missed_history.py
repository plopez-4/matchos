"""A returning viewer must not lose a completed spell when the live window moves."""
import pytest

from app.intelligence import match_stories, shot_windows, story_graph
from app.main import build_catch_up
from app.matchday import PROFILES, fixture
from app.models import CatchUpRequest, MatchEvent
from test_matchday import client, start, tick_to


def featured():
    return [MatchEvent(**raw) for raw in fixture(PROFILES[0], 'history')]


def shots(events):
    return {story['story_id']: story for story in match_stories(events)
            if story['kind'] == 'shot_activity'}


@pytest.mark.parametrize('return_at', [1500, 2100, 5580])
def test_completed_shot_stories_survive_later_quiet_windows(return_at):
    feed = featured()
    earlier = shots([event for event in feed if event.match_second <= 1200])
    later = shots([event for event in feed if event.match_second <= return_at])
    assert set(earlier) == {'shots:home:1200', 'shots:away:1200'}
    for identifier, story in earlier.items():
        assert later[identifier] == story
    # Live analytics still describe the latest pair, independently of missed history.
    live = shot_windows([event for event in feed if event.match_second <= return_at])
    assert len(live) == 2
    assert all(window['current']['end_second'] == return_at // 300 * 300 for window in live)


def test_missed_spell_is_in_both_audiences_and_excluded_after_acknowledgment():
    feed = [event for event in featured() if event.match_second <= 2100]
    left = max(event.sequence for event in feed if event.match_second <= 900)
    completed = min(event.sequence for event in feed if event.match_second >= 1200)
    for audience in ('casual', 'advanced'):
        result = build_catch_up(feed, CatchUpRequest(since_sequence=left, audience=audience))
        changes = next(section for section in result['explanation']['sections']
                       if section['title'] == 'What changed')
        assert {'shots:home:1200', 'shots:away:1200'} <= set(changes['story_ids'])
        assert '15–20' in changes['text']
        activity = [story for story in result['stories'] if story['kind'] == 'shot_activity']
        assert all(story['metric']['current']['shot_count'] == 3 for story in activity)
        seen = build_catch_up(feed, CatchUpRequest(since_sequence=completed, audience=audience))
        assert not any(story['kind'] == 'shot_activity' for story in seen['stories'])
        quiet = build_catch_up(feed, CatchUpRequest(since_sequence=result['through_sequence'], audience=audience))
        assert quiet['stories'] == [] and quiet['explanation']['sections'] == []


def test_historical_graph_keeps_exact_window_counts_and_supporting_events():
    feed = [event for event in featured() if event.match_second <= 1500]
    graph = story_graph(feed)
    nodes = {node['id']: node for node in graph['nodes']}
    edges = {(edge['source'], edge['target']) for edge in graph['edges']}
    for team, baseline in (('home', 0), ('away', 1)):
        identifier = f'shots:{team}:1200'
        assert identifier in nodes
        previous = nodes[f'metric:{identifier}:previous']
        current = nodes[f'metric:{identifier}:current']
        assert (previous['start_second'], previous['end_second'], previous['shot_count']) == (600, 900, baseline)
        assert (current['start_second'], current['end_second'], current['shot_count']) == (900, 1200, 3)
        for metric in (previous, current):
            assert (metric['id'], identifier) in edges
            assert all((event_id, metric['id']) in edges for event_id in metric['evidence_event_ids'])


def test_unfinished_and_unobserved_comparisons_are_not_backfilled():
    feed = featured()
    assert shots([event for event in feed if event.match_second < 1200]) == {}
    # Truncating the feed removes the baseline; historical reconstruction cannot invent it.
    assert 'shots:home:1200' not in shots([event for event in feed if 601 <= event.match_second <= 1500])


def test_browser_matchday_catchup_remembers_spell_after_live_activity_cools(monkeypatch):
    from app import matchday
    monkeypatch.setattr(matchday, 'selected_variant', lambda _: 0)
    with client() as browser:
        view = tick_to(browser, start(browser, 'history-day'), 900)
        mid = 'history-day-featured'
        first = browser.post(f'/api/matches/{mid}/catch-up', json={}).json()
        view = tick_to(browser, view, 1500)
        response = browser.post(f'/api/matches/{mid}/catch-up', json={
            'since_sequence': first['through_sequence'], 'audience': 'advanced'})
        assert response.status_code == 200
        result = response.json()
        assert {'shots:home:1200', 'shots:away:1200'} <= set(result['explanation']['selected_story_ids'])
        assert result['fan_briefing']['snapshot']['match_second'] == 1500
        # The historical comparison and current activity are different time scopes.
        assert result['fan_briefing']['locale_facts']['shots'] == {'home': 0, 'away': 0}
        empty = browser.post(f'/api/matches/{mid}/catch-up', json={
            'since_sequence': result['through_sequence']}).json()
        assert empty['evidence_event_ids'] == [] and empty['stories'] == []

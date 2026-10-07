import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app, store


def test_browser_fixture_is_read_only_and_ingests_with_evidence():
    store.clear()
    with TestClient(app) as client:
        result = client.get('/api/replay/scenario', params={'match_id': 'browser-test'})
        assert result.status_code == 200
        events = result.json()
        assert len(events) == 30
        assert store == {}
        for event in events:
            assert event['match_id'] == 'browser-test'
            assert client.post('/api/events', json=event).status_code == 201
        assert client.post('/api/events', json=events[-1]).json()['accepted'] is False
        analytics = client.get('/api/matches/browser-test/analytics').json()
        assert analytics['event_count'] == 30
        assert analytics['teams']['home']['goal'] == 1
        assert len(client.get('/api/matches/browser-test/stories').json()) == 2


def test_browser_fixture_rejects_invalid_match_ids():
    with TestClient(app) as client:
        for match_id in ('', '../bad', 'x' * 81):
            assert client.get('/api/replay/scenario', params={'match_id': match_id}).status_code == 422

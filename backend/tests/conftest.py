import pytest
from app import security, narration, story_writer
from app import ai_capacity
from app.main import store


@pytest.fixture(autouse=True)
def isolated_security(monkeypatch):
    """Every test starts with a fresh bounded demo; no provider credentials needed."""
    store.clear()
    security.matches.clear()
    security.sessions.clear()
    security.rates.clear()
    security.catch_cache.clear()
    security.ai_calls = security.ai_active = 0
    ai_capacity.COOLDOWNS.clear()
    narration.CACHE.clear()
    story_writer.CACHE.clear()
    narration.calls = narration.characters = 0
    monkeypatch.setenv('MATCHOS_SPEECH_MODE','off')
    monkeypatch.setenv('MATCHOS_AI_MODE','off')
    monkeypatch.setenv("MATCHOS_ENV", "local")
    monkeypatch.setenv('MATCHOS_PROXY_MODE','none')
    monkeypatch.setenv("MATCHOS_INGEST_TOKEN", "test-ingestion-credential-32-characters")
    monkeypatch.setenv("MATCHOS_AI_CALL_BUDGET", "100")


TRUSTED_HEADERS = {"X-MatchOS-Ingest-Token": "test-ingestion-credential-32-characters"}

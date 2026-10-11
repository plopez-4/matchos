import pytest
from app import security
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
    monkeypatch.setenv("MATCHOS_ENV", "local")
    monkeypatch.setenv("MATCHOS_INGEST_TOKEN", "test-ingestion-credential-32-characters")
    monkeypatch.setenv("MATCHOS_AI_CALL_BUDGET", "100")


TRUSTED_HEADERS = {"X-MatchOS-Ingest-Token": "test-ingestion-credential-32-characters"}

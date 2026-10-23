"""Offline, curated benchmarks; never part of synthetic match evidence."""
import json
from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def benchmarks():
    # Optional context must not break replay if its bundled file is missing/invalid.
    try:
        return json.loads(files('app').joinpath('data/historical_precedents.json').read_text(encoding='utf-8'))['entries']
    except (OSError, ValueError, KeyError):
        return []


def historical_precedent(phase, score):
    return next((entry for entry in benchmarks()
                 if entry['phase'] == phase
                 and entry['absolute_goal_margin'] == abs(score['home'] - score['away'])), None)

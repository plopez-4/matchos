"""Recalculate the single bundled benchmark from a local pinned OpenFootball file.

Usage: python scripts/calibrate_historical_precedents.py path/to/1-premierleague.txt
No network calls. No raw match rows are retained in the application.
"""
import hashlib
import json
from pathlib import Path
import re
import sys


def calculate(raw):
    rows = re.findall(r'(?m)^\s+(?:\d{1,2}:\d{2}\s+)?(.+?)\s+(\d+)-(\d+)(?:\s+\((\d+)-(\d+)\))?\s+(.+?)\s*$', raw)
    if len(rows) != 380:
        raise ValueError('Expected all 380 matches of the 2016–17 season.')
    eligible = []
    for _, home, away, ht_home, ht_away, _ in rows:
        if not ht_home:
            if (int(home), int(away)) != (0, 0):
                raise ValueError('Missing halftime score for a nonzero result.')
            # A 0–0 final score necessarily excludes a halftime one-goal lead.
            continue
        if abs(int(ht_home) - int(ht_away)) == 1:
            eligible.append((int(home) - int(away)) * (int(ht_home) - int(ht_away)))
    wins = sum(gap > 0 for gap in eligible)
    draws = sum(gap == 0 for gap in eligible)
    return {'matches_reviewed':len(rows), 'sample_size':len(eligible), 'wins':wins,
            'draws':draws, 'losses':len(eligible)-wins-draws,
            'win_percentage':round(100*wins/len(eligible), 1)}


if __name__ == '__main__':
    raw = Path(sys.argv[1]).read_bytes()
    target = Path(__file__).resolve().parents[1] / 'backend/app/data/historical_precedents.json'
    table = json.loads(target.read_text(encoding='utf-8'))
    entry = table['entries'][0]
    if hashlib.sha256(raw).hexdigest() != entry['source_sha256']:
        raise ValueError('Source checksum differs from the pinned, verified input.')
    actual = calculate(raw.decode('utf-8'))
    if any(entry[key] != value for key, value in actual.items()):
        raise ValueError('Calculated counts differ from the curated benchmark; review before editing.')
    print(json.dumps({**actual, 'source_sha256':hashlib.sha256(raw).hexdigest()}, indent=2))

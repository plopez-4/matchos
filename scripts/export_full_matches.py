"""Export reproducible synthetic evaluation feeds; never scrape real data."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.full_match import FULL_MATCHES, generate_full_match
from app.models import MatchEvent
from app.matchday import VERSION, VARIANTS


def main():
    output = root / "data" / "synthetic"
    output.mkdir(parents=True, exist_ok=True)
    catalog = []
    for sid in FULL_MATCHES:
        for variant in range(3):
            identifier = sid if variant == 0 else f'{sid}-v{variant+1}'
            events = generate_full_match(sid, match_id=identifier, variant=variant)
            for event in events:
                MatchEvent(**event)
            path = output / f"{identifier}.jsonl"
            path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
            config = VARIANTS[FULL_MATCHES[sid]['role']][variant]
            catalog.append({'id':identifier, 'fixture_id':sid, 'variant_id':variant+1,
                            'seed':config['seed'], 'event_count':len(events),
                            'duration_seconds':5580, 'file':path.name})
            print(f"{identifier}: {len(events)} synthetic events")
    manifest = {"data_origin": "synthetic", "selection": "One of three versions per fixture, fixed when a matchday starts",
                "generator": "backend/app/full_match.py", "version": VERSION,
                "purpose": "Match analytics and grounded narrative evaluation; no model training performed",
                "real_fixture_reconstruction": False, "fictional_players": False, "reference_player_identities": True,
                "coordinate_convention": "0..100 fixed attack frame, Home ->100 and Away ->0 across both halves",
                "clock_convention": "Cumulative playing seconds, 45-minute halves, zero-duration halftime, 3 added minutes in second half",
                "scenarios": catalog}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

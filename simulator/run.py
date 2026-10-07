"""Replay a seeded fictional match, using only the Python standard library."""
import argparse
import json
import random
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

def generate(seed=7, count=30, match_id="demo-match"):
    rng = random.Random(seed)
    for sequence in range(1, count + 1):
        yield dict(schema_version="1.0", event_id=f"sim-{seed}-{sequence}",
                   match_id=match_id, sequence=sequence, period=1,
                   match_second=sequence * 15, team_id=rng.choice(["home", "away"]),
                   player_id=f"player-{rng.randint(1, 11)}",
                   type="goal" if sequence % 10 == 0 else rng.choice(["pass", "shot", "recovery"]),
                   x=round(rng.uniform(0, 100), 2), y=round(rng.uniform(0, 100), 2), source="synthetic")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--match-id", default="demo-match")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.count <= 180 or args.interval < 0:
        parser.error("count must be 1..180 and interval nonnegative")
    for event in generate(args.seed, args.count, args.match_id):
        if args.dry_run:
            print(json.dumps(event))
            continue
        request = Request(args.api.rstrip("/") + "/api/events", data=json.dumps(event).encode(), headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=5) as response:
                print(response.read().decode())
        except URLError as exc:
            raise SystemExit(f"Ingestion failed: {exc}. Start the API or check --api.") from exc
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

"""Replay a fictional, sparse ten-minute highlights scenario (not a full feed)."""
import argparse
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

# Keep the CLI and browser on the same versioned synthetic fixture.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.simulation import generate

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--match-id", default="demo-match")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.count <= 30 or args.interval < 0:
        parser.error("count must be 1..30 and interval nonnegative")
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

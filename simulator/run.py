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
from app.simulation import generate, get_catalog

def main():
    catalog_ids = [s["id"] for s in get_catalog()]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        default="legacy-default",
        choices=catalog_ids,
        help="Synthetic match scenario to replay (default: legacy-default)",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for fictional player names (default: 7)")
    parser.add_argument("--count", type=int, default=None, help="Number of events to replay (default: full scenario)")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between events (default: 0.5)")
    parser.add_argument("--match-id", default="demo-match", help="Match identifier (default: demo-match)")
    parser.add_argument("--api", default="http://localhost:8000", help="MatchOS API base URL (default: http://localhost:8000)")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON events to stdout without sending to API")
    args = parser.parse_args()
    if args.interval < 0:
        parser.error("interval must be nonnegative")
    try:
        events = list(generate(seed=args.seed, count=args.count, match_id=args.match_id, scenario_id=args.scenario))
    except ValueError as err:
        parser.error(str(err))
    for event in events:
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

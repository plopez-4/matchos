"""Replay fictional highlights or a seeded full-match synthetic event feed."""
import argparse
import json
import time
import os
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor
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
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    token = os.getenv("MATCHOS_INGEST_TOKEN", "")
    headers = {"Content-Type": "application/json", "X-MatchOS-Client": "replay"}
    if not args.dry_run and not token:
        if args.seed != 7:
            parser.error("Custom seeds require a server-side MATCHOS_INGEST_TOKEN; default replay uses seed 7")
        for path, payload in [("/api/session", {}), ("/api/replay/start", {"match_id": args.match_id, "scenario_id": args.scenario})]:
            try:
                with opener.open(Request(args.api.rstrip("/")+path, data=json.dumps(payload).encode(), headers=headers), timeout=10) as response:
                    response.read()
            except URLError as exc:
                raise SystemExit(f"Replay setup failed: {exc}. Use a fresh --match-id for a new session.") from exc
    for event in events:
        if args.dry_run:
            print(json.dumps(event))
            continue
        if token:
            endpoint = "/api/events"
            payload = event
            event_headers = {**headers, "X-MatchOS-Ingest-Token": token}
        else:
            from urllib.parse import quote
            endpoint = "/api/matches/" + quote(args.match_id, safe="") + "/advance"
            payload = {"sequence":event["sequence"]}
            event_headers = headers
        request = Request(args.api.rstrip("/") + endpoint, data=json.dumps(payload).encode(), headers=event_headers)
        try:
            with opener.open(request, timeout=10) as response:
                print(response.read().decode())
        except URLError as exc:
            raise SystemExit(f"Ingestion failed: {exc}. Start the API or check --api.") from exc
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

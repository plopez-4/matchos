"""Frozen-version live evaluation: ten situations x two audiences, two languages each.

Uses the running backend's private Azure configuration, never reads its key.
Provider/model checks are integration results, not an independent semantic verdict.
One request per case; failed cases are recorded without automatic retries.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from hashlib import sha256
from pathlib import Path
import sys
import time
import uuid

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import story_writer
from app.models import MatchEvent


def run(output, cooldown, case_names=None, matchday_id=None):
    cases = json.loads((ROOT/'docs/recap-evaluation-cases.json').read_text())
    if case_names:
        cases = [case for case in cases if case['case'] in case_names]
    identifier = matchday_id or 'editorial-eval-'+uuid.uuid4().hex[:10]
    report = {'writer_version': story_writer.VERSION,
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'fixture_matchday_id': identifier,
              'evaluation': f'{len(cases)} situations x 2 audiences x 2 output languages',
              'source_hashes': {name:sha256((ROOT/'backend/app'/name).read_bytes()).hexdigest()
                                for name in ('story_writer.py', 'recap_context.py', 'recap_quality.py', 'story_plan.py')},
              'cases': [], 'prompts': {}, 'complete': False,
              'independent_fan_study': 'not_run', 'semantic_quality_verdict': 'pending_editorial_review'}

    def save():
        report['mode_counts'] = dict(Counter(row['writer_mode'] for row in report['cases']))
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    with httpx.Client(base_url='http://127.0.0.1:8000', headers={'X-MatchOS-Client':'replay'}, timeout=90) as browser:
        status = browser.get('/api/ai/status')
        status.raise_for_status()
        if not status.json()['configured'] or status.json()['writer_version'] != story_writer.VERSION:
            raise RuntimeError('The configured backend does not have the frozen evaluation version.')
        browser.post('/api/session', json={}).raise_for_status()
        browser.post('/api/matchdays/start', json={'matchday_id':identifier}).raise_for_status()
        tick, last_request = 0, None
        try:
            for case in cases:
                while tick < case['second']//30:
                    tick += 1
                    browser.post(f'/api/matchdays/{identifier}/tick', json={'tick':tick}).raise_for_status()
                mid = f'{identifier}-{case["role"]}'
                response = browser.get(f'/api/matches/{mid}/events')
                response.raise_for_status()
                events = response.json()
                cursor = max(event['sequence'] for event in events if event['match_second'] <= case['cursor_second'])
                for audience in ('casual', 'advanced'):
                    if last_request is not None:
                        remaining = cooldown-(time.monotonic()-last_request)
                        if remaining > 0:
                            time.sleep(remaining)
                    began = time.monotonic()
                    response = browser.post(f'/api/matches/{mid}/catch-up', json={'since_sequence':cursor, 'audience':audience})
                    response.raise_for_status()
                    last_request = time.monotonic()
                    result = response.json()
                    fan = result['fan_briefing']
                    narrative = fan['narrative']
                    expected_hash = story_writer.prompt_fingerprint(fan)
                    if narrative.get('version') != report['writer_version'] or narrative.get('prompt_hash') != expected_hash:
                        raise RuntimeError('Prompt changed during evaluation; refusing to mix versions.')
                    report['prompts'][expected_hash] = {'writer':story_writer.writer_prompt(fan), 'reviewer':story_writer.review_prompt(),
                                                       'revision':story_writer.revision_prompt()}
                    report['cases'].append({**case, 'audience':audience,
                        'seconds':round(time.monotonic()-began, 2), 'snapshot':fan['snapshot'],
                        'writer_mode':narrative['mode'], 'prompt_hash':expected_hash,
                        'fallback_reason':narrative.get('fallback_reason'),
                        'validation_stage':narrative.get('validation_stage'),
                        'validation_details':narrative.get('validation_details'),
                        'model_review':narrative.get('review'), 'text':narrative['text'],
                        'revision_used':narrative.get('revision_used', False),
                        'selected_stories':fan['story_plan']['stories'],
                        'evidence':story_writer.evidence_packet(fan, [MatchEvent(**row) for row in events]),
                        'editorial_review':'pending'})
                    save()
                    print(len(report['cases']), case['case'], audience, narrative['mode'], narrative.get('fallback_reason'), flush=True)
            report['complete'] = len(report['cases']) == len(cases)*2
        finally:
            released = browser.request('DELETE', f'/api/matchdays/{identifier}', json={})
            report['temporary_demo_released'] = released.status_code == 200
            report['finished_utc'] = datetime.now(timezone.utc).isoformat()
            save()
    return report['complete']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'docs/recap-editorial-evaluation.json')
    parser.add_argument('--cooldown', type=float, default=60)
    parser.add_argument('--case', action='append', dest='case_names',
                        choices=[case['case'] for case in json.loads((ROOT/'docs/recap-evaluation-cases.json').read_text())])
    parser.add_argument('--matchday-id', help='Reuse a released fixture ID for an exact seeded comparison')
    args = parser.parse_args()
    if not 0 <= args.cooldown <= 60:
        parser.error('cooldown must be between 0 and 60 seconds')
    sys.exit(0 if run(args.output, args.cooldown, args.case_names, args.matchday_id) else 1)

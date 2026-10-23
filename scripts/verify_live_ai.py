"""Bounded local acceptance run. Uses the running server's private configuration.

Run from the repository root; never accepts, reads or prints the server's API key.
Provider-failure coverage is explicitly simulated, not an actual Azure outage.
"""
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch
import uuid

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app import story_writer
from app.models import MatchEvent


def run():
    report = {'expected_writer_version': story_writer.VERSION, 'live_cases': [],
              'failure_test': {'type': 'simulated_provider_503'}}
    identifier = 'quality-check-' + uuid.uuid4().hex[:10]
    with httpx.Client(base_url='http://127.0.0.1:8000', headers={'X-MatchOS-Client': 'replay'}, timeout=90) as browser:
        response = browser.get('/api/ai/status')
        if response.status_code == 404:
            raise RuntimeError('The running server has the old code. Restart it in the same private PowerShell session.')
        response.raise_for_status()
        status = response.json()
        if not status['configured'] or status['writer_version'] != story_writer.VERSION:
            raise RuntimeError('The running backend is not configured with the expected writer version.')
        browser.post('/api/session', json={}).raise_for_status()
        browser.post('/api/matchdays/start', json={'matchday_id': identifier}).raise_for_status()
        tick = 0
        sample = None
        try:
            for name, target, role, left in (('busy', 1500, 'featured', 900), ('quiet', 2400, 'quiet', 1800)):
                while tick < target // 30:
                    tick += 1
                    browser.post(f'/api/matchdays/{identifier}/tick', json={'tick': tick}).raise_for_status()
                mid = f'{identifier}-{role}'
                events = browser.get(f'/api/matches/{mid}/events')
                events.raise_for_status()
                rows = events.json()
                cursor = max(event['sequence'] for event in rows if event['match_second'] <= left)
                for audience in ('casual', 'advanced'):
                    began = time.monotonic()
                    response = browser.post(f'/api/matches/{mid}/catch-up', json={'since_sequence': cursor, 'audience': audience})
                    response.raise_for_status()
                    result = response.json()
                    fan = result['fan_briefing']
                    narrative = fan['narrative']
                    passed = (result['explanation']['mode'] == 'azure' and narrative['mode'] == 'azure'
                              and narrative.get('review') == 'model_review_passed'
                              and narrative.get('metric_rendering') == 'model_reviewed') if name == 'busy' else (
                              narrative['mode'] == 'deterministic' and narrative.get('fallback_reason') == 'no_selected_story')
                    player_story = next((story for story in fan['story_plan']['stories']
                                         if story['story_id'] == fan['story_plan'].get('player_story_id')), None)
                    passed = passed and (player_story is not None and player_story['kind'] == 'player_shot_creation'
                        and player_story['metric']['count'] >= 2 if name == 'busy' else
                        fan['story_plan']['status'] == 'no_qualifying_change' and fan['story_plan']['story_ids'] == [])
                    report['live_cases'].append({
                        'case': name, 'audience': audience, 'seconds': round(time.monotonic()-began, 2),
                        'selector_mode': result['explanation']['mode'],
                        'writer_mode': narrative['mode'], 'review': narrative.get('review'),
                        'metric_rendering': narrative.get('metric_rendering'),
                        'fallback_reason': narrative.get('fallback_reason'),
                        'validation_stage': narrative.get('validation_stage'),
                        'validation_details': narrative.get('validation_details'),
                        'plan_status': fan['story_plan']['status'],
                        'plan_story_ids': fan['story_plan']['story_ids'],
                        'player_contribution': player_story['metric'] if player_story else None,
                        'text': narrative['text'], 'ai_writing_required': name == 'busy', 'case_passed': bool(passed)})
                    print(name, audience, narrative['mode'], narrative.get('fallback_reason'), flush=True)
                    if name == 'busy' and sample is None:
                        sample = (fan, [MatchEvent(**raw) for raw in rows])
                    if name == 'busy' and audience == 'casual':
                        # Four bounded model calls per busy recap; do not hammer a small deployment.
                        print('Cooling down for 60 seconds before the Analyst request.', flush=True)
                        time.sleep(60)
            fan, feed = sample
            # Rebuild the rule paragraph because the displayed sample may be AI-written.
            from app import story_plan
            story_plan.bind(fan, fan['story_plan']['stories'], fan['audience'])
            expected = fan['spoken_recap'].copy()
            with patch.dict(os.environ, {'MATCHOS_AI_MODE': 'azure',
                'AZURE_OPENAI_BASE_URL': 'https://fixture.openai.azure.com/openai/v1',
                'AZURE_OPENAI_DEPLOYMENT': 'failure-test', 'AZURE_OPENAI_API_KEY': 'fake-test-credential'}):
                with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503))) as provider:
                    fallback = story_writer.write(fan, feed, provider)
            report['failure_test']['passed'] = fallback['mode'] == 'deterministic' and fallback['text'] == expected
        finally:
            release = browser.request('DELETE', f'/api/matchdays/{identifier}', json={})
            report['temporary_demo_released'] = release.status_code == 200
            path = ROOT / 'docs' / 'live-azure-quality-results.json'
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
            print('Saved', path, flush=True)
    return all(row['case_passed'] for row in report['live_cases']) and report['failure_test'].get('passed', False)


if __name__ == '__main__':
    try:
        passed = run()
    except (httpx.HTTPError, RuntimeError) as error:
        print(type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
    sys.exit(0 if passed else 1)

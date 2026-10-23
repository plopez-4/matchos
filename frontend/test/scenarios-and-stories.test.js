import test from 'node:test';
import assert from 'node:assert/strict';
import { getStoryKindMeta } from '../src/utils/stories.js';
import { fetchReplayScenario, ingestReplayEvent } from '../src/api.js';
import { resolveScenario } from '../src/utils/scenarios.js';

test('getStoryKindMeta resolves all distinct story kinds with badges and icons', () => {
  const goal = getStoryKindMeta('goal');
  assert.equal(goal.label, 'Goal Story');
  assert.equal(goal.badgeClass, 'badge-goal');
  assert.equal(goal.icon, '⚽');

  const shift = getStoryKindMeta('shot_activity');
  assert.equal(shift.label, 'Attacking Shift');
  assert.equal(shift.badgeClass, 'badge-activity');
  assert.equal(shift.icon, '📈');

  const recovery = getStoryKindMeta('high_recovery');
  assert.equal(recovery.label, 'High Recovery');
  assert.equal(recovery.badgeClass, 'badge-recovery');
  assert.equal(recovery.icon, '🛡️');

  const pass = getStoryKindMeta('progressive_pass');
  assert.equal(pass.label, 'Progressive Pass');
  assert.equal(pass.badgeClass, 'badge-pass');
  assert.equal(pass.icon, '⚡');

  const transition = getStoryKindMeta('recovery_shot');
  assert.equal(transition.label, 'Recovery to Shot');
  assert.equal(transition.badgeClass, 'badge-transition');
  assert.equal(transition.icon, '⏱️');

  const fallback = getStoryKindMeta('unknown_custom_kind');
  assert.equal(fallback.label, 'Match Story');
  assert.equal(fallback.badgeClass, 'badge-default');
  assert.equal(fallback.icon, '📋');
});

test('replay uses a single private cookie session and sends only sequence advancement', async () => {
  let requestedUrl = '';
  let requestedOptions;
  let sessions = 0;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    if (url === '/api/session') sessions++;
    requestedUrl = url;
    requestedOptions = options;
    return {
      ok: true,
      json: async () => [{ sequence: 1 }],
    };
  };

  // Explicit scenario ID
  await fetchReplayScenario('match-1', 'pressure-builds');
  assert.equal(requestedUrl, '/api/replay/start');
  assert.deepEqual(JSON.parse(requestedOptions.body), {
    match_id: 'match-1',
    scenario_id: 'pressure-builds',
  });

  // Legacy call passing options as second argument
  await fetchReplayScenario('match-2', { signal: new AbortController().signal });
  assert.deepEqual(JSON.parse(requestedOptions.body), {
    match_id: 'match-2',
    scenario_id: 'united-city-90',
  });

  // Default scenario parameter omitted
  await fetchReplayScenario('match-3');
  assert.deepEqual(JSON.parse(requestedOptions.body), {
    match_id: 'match-3',
    scenario_id: 'united-city-90',
  });
  await ingestReplayEvent({
    match_id: 'match-3',
    sequence: 1,
    type: 'goal',
    player_name: 'fabricated',
  });
  assert.equal(requestedUrl, '/api/matches/match-3/advance');
  assert.deepEqual(JSON.parse(requestedOptions.body), { sequence: 1 });
  assert.equal(requestedOptions.credentials, 'same-origin');
  assert.equal(requestedOptions.headers['X-MatchOS-Client'], 'replay');
  assert.equal(sessions, 1);
  globalThis.fetch = originalFetch;
});

test('scenario URLs accept current fixtures and retire old selectable demos', () => {
  for (const id of ['united-city-90', 'palace-newcastle-90', 'brighton-fulham-90']) {
    assert.equal(resolveScenario(id), id);
  }
  for (const id of [
    null,
    '',
    'pressure-builds',
    'comeback',
    'quiet-match',
    'legacy-default',
    'united-hull-90',
    '../hack',
  ]) {
    assert.equal(resolveScenario(id), 'united-city-90');
  }
});

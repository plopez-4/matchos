import test from 'node:test';
import assert from 'node:assert/strict';
import {
  formatMatchSecond,
  formatTeamName,
  formatEventType,
  formatOutcome,
} from '../src/utils/formatters.js';

test('formatMatchSecond formats seconds into MM:SS correctly', () => {
  assert.equal(formatMatchSecond(0), '0:00');
  assert.equal(formatMatchSecond(60), '1:00');
  assert.equal(formatMatchSecond(571), '9:31');
  assert.equal(formatMatchSecond(600), '10:00');
  assert.equal(formatMatchSecond(null), '0:00');
});

test('formatTeamName maps IDs to fictional club names', () => {
  assert.equal(formatTeamName('home'), 'Home FC');
  assert.equal(formatTeamName('away'), 'Away FC');
  assert.equal(formatTeamName('other'), 'OTHER');
});

test('formatEventType and formatOutcome capitalize and format cleanly', () => {
  assert.equal(formatEventType('kickoff'), 'Kickoff');
  assert.equal(formatEventType('pass'), 'Pass');
  assert.equal(formatEventType('shot'), 'Shot');
  assert.equal(formatEventType('goal'), 'Goal');
  assert.equal(formatEventType('recovery'), 'Recovery');

  assert.equal(formatOutcome('goal'), 'Goal');
  assert.equal(formatOutcome('saved'), 'Saved');
  assert.equal(formatOutcome('blocked'), 'Blocked');
  assert.equal(formatOutcome('missed'), 'Missed');
  assert.equal(formatOutcome(null), null);
});

import { catchUpReducer, initialCatchUpState } from '../src/utils/catchUpState.js';
import { visibleTimelineEvents } from '../src/utils/timeline.js';

const response = { through_sequence: 30, evidence_event_ids: ['e30'] };

test('actual catch-up reducer preserves cursor and summary on failure', () => {
  const completed = catchUpReducer(initialCatchUpState, { type: 'success', generation: 0, result: response });
  const pending = catchUpReducer(completed, { type: 'start', generation: 0 });
  const failed = catchUpReducer(pending, { type: 'failure', generation: 0, error: 'Offline' });
  assert.equal(failed.summary, response);
  assert.equal(failed.summary.through_sequence, 30);
  assert.equal(failed.busy, false);
  assert.equal(failed.error, 'Offline');
});

test('reset releases loading and ignores old success/failure during a new request', () => {
  const pending = catchUpReducer(initialCatchUpState, { type: 'start', generation: 0 });
  const reset = catchUpReducer(pending, { type: 'reset', generation: 1 });
  assert.equal(reset.busy, false);
  assert.equal(reset.summary, null);
  const newPending = catchUpReducer(reset, { type: 'start', generation: 1 });
  assert.equal(catchUpReducer(newPending, { type: 'success', generation: 0, result: response }), newPending);
  assert.equal(catchUpReducer(newPending, { type: 'failure', generation: 0, error: 'Old error' }), newPending);
  const completed = catchUpReducer(newPending, { type: 'success', generation: 1, result: response });
  assert.equal(completed.busy, false);
  assert.equal(completed.summary, response);
});

test('a successful newer response is retained until an explicit reset', () => {
  const result = catchUpReducer(initialCatchUpState, { type: 'success', generation: 0, result: response });
  // Polling snapshots do not invalidate a response simply because they lag behind it.
  assert.equal(catchUpReducer(result, { type: 'poll', generation: 0, latestSequence: 12 }), result);
  assert.equal(catchUpReducer(result, { type: 'reset', generation: 1 }).summary, null);
});

const events = Array.from({ length: 30 }, (_, i) => ({
  event_id: `e${i + 1}`, sequence: i + 1, type: i === 3 ? 'shot' : 'pass',
}));

test('evidence navigation reveals an old event hidden by both limit and filter', () => {
  assert.equal(visibleTimelineEvents(events, 'pass', false, null).some(e => e.event_id === 'e4'), false);
  const visible = visibleTimelineEvents(events, 'pass', false, 'e4');
  assert.equal(visible.some(e => e.event_id === 'e4'), true);
  assert.equal(visible[0].sequence, 30);
  assert.equal(visible.at(-1).sequence, 1);
  assert.equal(visibleTimelineEvents(events, 'all', false, null).length, 12);
});

test('missing evidence does not invent events and clearing restores selected filter', () => {
  assert.equal(visibleTimelineEvents(events, 'key', false, 'missing').length, 1);
  assert.equal(visibleTimelineEvents(events, 'pass', false, null).length, 12);
});

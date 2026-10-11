import test from 'node:test';
import assert from 'node:assert/strict';
import { playMatchday, createReleaseRecovery } from '../src/utils/matchday.js';

test('failed cleanup is retained and retried before another group can be abandoned', async () => {
  const calls = [];
  const recovery = createReleaseRecovery(async (id) => {
    calls.push(id);
    if (calls.length === 1) throw new Error('offline');
  });
  recovery.queue('old-day');
  await assert.rejects(recovery.retry(), /offline/);
  assert.throws(() => recovery.queue('another-day'), /cleanup is still pending/);
  await recovery.retry();
  await recovery.retry();
  assert.deepEqual(calls, ['old-day', 'old-day']);
  recovery.queue('another-day');
});

test('missing or inaccessible old groups do not block recovery; aborted release stays pending', async () => {
  for (const status of [401, 403, 404]) {
    let calls = 0;
    const recovery = createReleaseRecovery(async () => {
      calls++;
      throw Object.assign(new Error('unavailable'), { status });
    });
    recovery.queue('old');
    await recovery.retry();
    await recovery.retry();
    assert.equal(calls, 1);
  }
  const controller = new AbortController();
  const calls = [];
  const recovery = createReleaseRecovery(async (id) => {
    calls.push(id);
    controller.abort();
  });
  recovery.queue('old');
  await recovery.retry({ signal: controller.signal });
  await recovery.retry();
  assert.deepEqual(calls, ['old', 'old']);
});

test('matchday shares a monotonically advancing clock with sequential requests', async () => {
  const seen = [];
  let active = 0;
  await playMatchday({
    initialView: { matchday_id: 'd', tick: 0, finished: false },
    intervalMs: 0,
    signal: new AbortController().signal,
    step: async (id, tick) => {
      assert.equal(id, 'd');
      assert.equal(++active, 1);
      await Promise.resolve();
      active--;
      return { matchday_id: id, tick, clock_second: tick * 30, finished: tick === 3 };
    },
    onView: (view) => seen.push(view.clock_second),
  });
  assert.deepEqual(seen, [30, 60, 90]);
});

test('pause ignores a committed but stale response; retry requests the same tick', async () => {
  const controller = new AbortController();
  const initial = { matchday_id: 'd', tick: 4, finished: false };
  const ticks = [];
  const finished = await playMatchday({
    initialView: initial,
    intervalMs: 0,
    signal: controller.signal,
    step: async (_, tick) => {
      ticks.push(tick);
      controller.abort();
      return { ...initial, tick, finished: true };
    },
    onView: () => assert.fail('An aborted response must not advance the displayed cursor'),
  });
  assert.equal(finished, false);
  await playMatchday({
    initialView: initial,
    intervalMs: 0,
    signal: new AbortController().signal,
    step: async (_, tick) => {
      ticks.push(tick);
      return { ...initial, tick, finished: true };
    },
    onView: () => {},
  });
  assert.deepEqual(ticks, [5, 5]);
});

test('a failed tick cannot advance the last successful clock', async () => {
  const seen = [];
  await assert.rejects(
    playMatchday({
      initialView: { matchday_id: 'd', tick: 0 },
      intervalMs: 0,
      signal: new AbortController().signal,
      step: async () => {
        throw new Error('offline');
      },
      onView: (view) => seen.push(view),
    }),
    /offline/,
  );
  assert.deepEqual(seen, []);
});

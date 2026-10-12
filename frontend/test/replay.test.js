import test from 'node:test';
import assert from 'node:assert/strict';
import { playReplay } from '../src/utils/replay.js';

test('replay waits at the selected speed and sends events in order', async () => {
  const delays = [],
    sent = [],
    progress = [];
  const finished = await playReplay({
    events: [1, 2, 3],
    startIndex: 1,
    intervalMs: 750,
    signal: new AbortController().signal,
    wait: async (ms) => delays.push(ms),
    ingest: async (event) => sent.push(event),
    onProgress: (count) => progress.push(count),
  });
  assert.equal(finished, true);
  assert.deepEqual(delays, [750, 750]);
  assert.deepEqual(sent, [2, 3]);
  assert.deepEqual(progress, [2, 3]);
});

test('pausing during a delay sends no next event', async () => {
  const controller = new AbortController();
  const sent = [];
  const finished = await playReplay({
    events: [1],
    startIndex: 0,
    intervalMs: 3000,
    signal: controller.signal,
    wait: async () => controller.abort(),
    ingest: async (event) => sent.push(event),
    onProgress: () => assert.fail('Cancelled replay advanced'),
  });
  assert.equal(finished, false);
  assert.deepEqual(sent, []);
});

test('failed ingestion preserves the cursor for a retry', async () => {
  let cursor = 0;
  const options = {
    events: [1, 2],
    startIndex: 0,
    intervalMs: 0,
    signal: new AbortController().signal,
    wait: async () => {},
    onProgress: (count) => {
      cursor = count;
    },
    ingest: async (event) => {
      if (event === 2) throw new Error('offline');
    },
  };
  await assert.rejects(playReplay(options), /offline/);
  assert.equal(cursor, 1);
  const sent = [];
  await playReplay({ ...options, startIndex: cursor, ingest: async (event) => sent.push(event) });
  assert.deepEqual(sent, [2]);
  assert.equal(cursor, 2);
});

test('pausing during a request ignores stale progress and retries safely', async () => {
  const controller = new AbortController();
  let cursor = 0;
  const accepted = new Set();
  const options = {
    events: [1],
    startIndex: 0,
    intervalMs: 0,
    signal: controller.signal,
    wait: async () => {},
    onProgress: (count) => {
      cursor = count;
    },
    ingest: async (event) => {
      accepted.add(event);
      controller.abort();
    },
  };
  assert.equal(await playReplay(options), false);
  assert.equal(cursor, 0);
  await playReplay({
    ...options,
    signal: new AbortController().signal,
    ingest: async (event) => accepted.add(event),
  });
  assert.equal(cursor, 1);
  assert.equal(accepted.size, 1);
});

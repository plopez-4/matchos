import test from 'node:test';
import assert from 'node:assert/strict';

let instance = 0;
async function setup(t, handler) {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    const body = JSON.parse(options.body);
    calls.push({ url, body, credentials: options.credentials });
    if (url === '/api/session') return Response.json({ status: 'ready' });
    return handler(body, calls);
  });
  const api = await import(`../src/api.js?session-test=${++instance}`);
  return { api, calls };
}

test('owned matchday reopens without replacing its identity or clock', async (t) => {
  const view = { matchday_id: 'owned', tick: 7 };
  const { api, calls } = await setup(t, () => Response.json(view));
  assert.deepEqual(await api.startMatchday('owned'), view);
  assert.equal(calls.length, 2);
  assert.ok(calls.every((call) => call.credentials === 'same-origin'));
});

test('shared matchday link starts a new owned group without writing or deleting the original', async (t) => {
  const { api, calls } = await setup(t, ({ matchday_id }) =>
    matchday_id === 'someone-elses-day'
      ? Response.json({ detail: 'This matchday belongs to another session' }, { status: 403 })
      : Response.json({ matchday_id, tick: 0 }),
  );
  const view = await api.startMatchday('someone-elses-day');
  assert.match(view.matchday_id, /^day-[a-f0-9]{32}$/);
  assert.equal(view.session_recovered, true);
  assert.equal(view.tick, 0);
  assert.deepEqual(
    calls.map((call) => call.url),
    ['/api/session', '/api/matchdays/start', '/api/matchdays/start'],
  );
});

test('shared fixed test link preserves the requested match version', async (t) => {
  const original = 'test-v4-shared';
  const { api, calls } = await setup(t, ({ matchday_id }) =>
    matchday_id === original
      ? Response.json({ detail: 'This matchday belongs to another session' }, { status: 403 })
      : Response.json({ matchday_id }),
  );
  const view = await api.startMatchday(original);
  assert.match(view.matchday_id, /^test-v4-[a-f0-9]{32}$/);
  assert.equal(calls.at(-1).body.resume_on_capacity, false);
});

test('expired cookie is renewed once before an inaccessible replay is replaced', async (t) => {
  let starts = 0;
  const { api, calls } = await setup(t, ({ matchday_id }) => {
    starts++;
    if (starts === 1)
      return Response.json({ detail: 'Replay session expired; reload the page' }, { status: 401 });
    if (starts === 2)
      return Response.json({ detail: 'This matchday belongs to another session' }, { status: 403 });
    return Response.json({ matchday_id });
  });
  assert.equal((await api.startMatchday('old-day')).session_recovered, true);
  assert.equal(calls.filter((call) => call.url === '/api/session').length, 2);
  assert.equal(starts, 3);
});

test('origin failures and capacity limits are reported without creating extra replays', async (t) => {
  for (const [status, detail] of [
    [403, 'Origin is not allowed'],
    [429, 'Not enough demo capacity for three matches'],
  ]) {
    const { api, calls } = await setup(t, () => Response.json({ detail }, { status }));
    await assert.rejects(
      api.startMatchday('test-day'),
      (error) => error.status === status && error.detail === detail,
    );
    assert.equal(calls.length, 2);
  }
});

test('failed renewal stops rather than looping or bypassing session protection', async (t) => {
  const { api, calls } = await setup(t, () =>
    Response.json({ detail: 'Replay session expired; reload the page' }, { status: 401 }),
  );
  await assert.rejects(api.startMatchday('old-day'), (error) => error.status === 401);
  assert.equal(calls.filter((call) => call.url === '/api/matchdays/start').length, 2);
});

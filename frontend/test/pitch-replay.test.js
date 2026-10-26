import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';
import {
  pitchMoves,
  actionCaption,
  connectedActions,
  replayTransition,
  actionTrail,
  actionParticipants,
  actionDuration,
} from '../src/utils/pitchReplay.js';

const pass = (sequence, fields = {}) => ({
  event_id: `e${sequence}`,
  sequence,
  match_id: 'm',
  period: 1,
  possession_id: 'p1',
  team_id: 'home',
  team_name: 'Palace',
  player_id: 'h2',
  player_name: 'Alex',
  recipient_player_id: 'h7',
  recipient_player_name: 'Sam',
  type: 'pass',
  match_second: sequence * 3,
  x: 20,
  y: 40,
  end_x: 40,
  end_y: 60,
  outcome: 'complete',
  ...fields,
});

test('moves preserve observed order and separate possession, team, period and missing-coordinate gaps', () => {
  const events = [
    pass(2),
    pass(1),
    pass(3, { possession_id: 'p2' }),
    pass(4, { team_id: 'away' }),
    pass(5, { period: 2 }),
    pass(6, { end_x: NaN }),
    pass(7, { period: 2 }),
  ];
  const moves = pitchMoves(events);
  assert.deepEqual(
    moves.map((m) => m.events.map((e) => e.sequence)),
    [[1, 2], [3], [4], [5], [7]],
  );
  assert.deepEqual(
    events.map((e) => e.sequence),
    [2, 1, 3, 4, 5, 6, 7],
  );
  assert.equal(pitchMoves([pass(1, { x: 101 })]).length, 0);
});

test('failed passes do not claim the recipient received the ball', () => {
  assert.equal(actionCaption(pass(1)), 'Alex finds Sam.');
  assert.equal(actionCaption(pass(1, { outcome: 'incomplete' })), 'Alex passes toward Sam.');
});

test('red cards form their own move and participants show Sent off role', () => {
  const card = pass(1, { type: 'red_card', player_name: 'Elliot Anderson' });
  const moves = pitchMoves([card]);
  assert.equal(moves.length, 1);
  assert.equal(moves[0].events[0].type, 'red_card');
  assert.equal(actionCaption(card), 'Elliot Anderson is sent off with a red card for Palace.');
  const people = actionParticipants(card);
  assert.equal(people.length, 1);
  assert.equal(people[0].role, 'Sent off');
});

test('a connected build-up requires matching recipient, position, scope and time', () => {
  const first = pass(1);
  const second = pass(2, { player_id: 'h7', x: 40, y: 60 });
  assert.equal(connectedActions(first, second), true);
  for (const fields of [
    { player_id: 'h9' },
    { x: 45 },
    { team_id: 'away' },
    { period: 2 },
    { possession_id: 'p2' },
    { sequence: 3 },
    { match_second: 50 },
  ]) {
    assert.equal(connectedActions(first, { ...second, ...fields }), false);
    assert.ok(replayTransition(first, { ...second, ...fields }));
  }
  assert.equal(connectedActions({ ...first, outcome: 'intercepted' }, second), false);
  assert.equal(
    connectedActions({ ...first, possession_id: null }, { ...second, possession_id: null }),
    false,
  );
  assert.equal(replayTransition(first, second), null);
  assert.match(
    replayTransition(first, { ...second, possession_id: 'p2', match_second: 33 }),
    /Next recorded possession.*30 seconds later/,
  );
  assert.match(replayTransition(second, first), /Earlier build-up/);
  assert.deepEqual(
    actionTrail([first, second], 1).map((e) => e.event_id),
    ['e1', 'e2'],
  );
  assert.deepEqual(
    actionTrail([first, { ...second, x: 45 }], 1).map((e) => e.event_id),
    ['e2'],
  );
});

test('markers use only current observed participants and never place a scorer at the goal line', () => {
  const first = pass(1, { player_shirt_number: 8, recipient_player_shirt_number: 10 });
  assert.deepEqual(
    actionParticipants(first).map((p) => [p.id, p.number, p.x, p.role]),
    [
      ['h2', 8, 20, 'Passer'],
      ['h7', 10, 40, 'Receiver'],
    ],
  );
  assert.deepEqual(
    actionParticipants({ ...first, outcome: 'intercepted' }).map((p) => p.role),
    ['Passer'],
  );
  const shot = pass(2, {
    type: 'shot',
    player_id: 'h7',
    x: 40,
    y: 60,
    end_x: 100,
    end_y: 50,
    outcome: 'goal',
  });
  const goal = pass(3, { type: 'goal', player_id: 'h7', x: 100, y: 50, related_event_id: 'e2' });
  assert.equal(connectedActions(first, shot), true);
  assert.equal(connectedActions(shot, goal), true);
  assert.equal(actionParticipants(goal, shot)[0].x, 40);
  assert.deepEqual(actionParticipants(goal), []);
  assert.deepEqual(actionParticipants({ ...goal, player_id: 'h9' }, shot), []);
  assert.ok(actionDuration(first, shot) >= 1400);
  assert.equal(actionDuration(first, shot, 2), actionDuration(first, shot) / 2);
});

const bundle = await build({
  entryPoints: {
    pitch: 'src/components/PitchReplay.jsx',
  },
  outdir: 'unused',
  bundle: true,
  write: false,
  platform: 'node',
  format: 'esm',
  external: ['react', 'react-dom'],
});
async function component(name) {
  const source = bundle.outputFiles
    .find((f) => f.path.endsWith(`${name}.js`))
    .text.replaceAll('from "react"', `from ${JSON.stringify(import.meta.resolve('react'))}`)
    .replaceAll('from "react-dom"', `from ${JSON.stringify(import.meta.resolve('react-dom'))}`);
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
}
const { PitchReplay } = await component('pitch');

test('fan and development pitches explain the recorded participants in English and Spanish', () => {
  for (const compact of [true, false]) {
    for (const language of ['en', 'es']) {
      const html = renderToStaticMarkup(
        React.createElement(PitchReplay, { events: [pass(1)], compact, language }),
      );
      const explanation =
        language === 'es'
          ? 'Solo se muestran los jugadores que participan en esta jugada registrada.'
          : 'Only players involved in this recorded move are shown.';
      assert.ok(html.includes(explanation));
      assert.ok(html.indexOf(explanation) < html.indexOf('<svg'));
      assert.ok(html.includes(language === 'es' ? 'Balón blanco' : 'White ball'));
      assert.ok(html.includes('Alex finds Sam.'));
    }
  }
});

test('pitch renders recorded endpoints, animated ball, controls and safe empty state', () => {
  const html = renderToStaticMarkup(
    React.createElement(PitchReplay, { events: [pass(1), pass(2)] }),
  );
  assert.match(html, /viewBox="0 0 1200 780"/);
  assert.match(html, /x1="276" y1="322" x2="492" y2="458"/);
  assert.match(html, /pitch-ball-moving/);
  assert.match(html, /--pitch-start-x:276px/);
  assert.match(html, /animation-play-state:running/);
  assert.match(html, /Passer: Alex/);
  assert.match(html, /Receiver: Sam/);
  assert.match(html, /small dots show earlier ball locations/);
  assert.match(html, /compressed replay/);
  assert.match(html, /Alex finds Sam/);
  assert.match(html, /Pause pitch/);
  const empty = renderToStaticMarkup(React.createElement(PitchReplay, { events: [] }));
  assert.match(empty, /Start the match to see the ball move/);
  assert.doesNotMatch(empty, /NaN/);
});

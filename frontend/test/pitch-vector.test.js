import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';

const bundle = await build({
  entryPoints: {
    pitch: 'src/components/PitchVector.jsx',
  },
  bundle: true,
  write: false,
  outdir: 'unused',
  platform: 'node',
  format: 'esm',
  external: ['react'],
});
async function component(file) {
  const source = bundle.outputFiles
    .find((f) => f.path.endsWith(file))
    .text.replaceAll('from "react"', `from ${JSON.stringify(import.meta.resolve('react'))}`);
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
}
const { PitchVector, vectorEvent } = await component('pitch.js');
const shot = {
  event_id: 's',
  match_id: 'm',
  sequence: 1,
  match_second: 10,
  type: 'shot',
  team_id: 'away',
  player_id: 'away-10',
  player_name: 'Yoane Wissa',
  outcome: 'goal',
  x: 18,
  y: 50,
  end_x: 0,
  end_y: 50,
};
test('SVG uses recorded vector endpoints in either direction and unique marker IDs', () => {
  const html = renderToStaticMarkup(React.createElement(PitchVector, { event: shot }));
  assert.match(html, /x1="25.44"/);
  assert.match(html, /x2="6"/);
  assert.match(html, /Yoane Wissa/);
  assert.match(html, /width="120" height="80"/);
  const right = renderToStaticMarkup(
    React.createElement(PitchVector, { event: { ...shot, type: 'pass', x: 0, end_x: 100 } }),
  );
  assert.match(right, /x2="114"/);
  const pair = renderToStaticMarkup(
    React.createElement(
      'div',
      null,
      React.createElement(PitchVector, { event: shot }),
      React.createElement(PitchVector, { event: shot }),
    ),
  );
  const ids = [...pair.matchAll(/<marker id="([^"]+)"/g)].map((match) => match[1]);
  assert.equal(new Set(ids).size, 2);
});

test('missing/invalid coordinates never create a vector; a goal needs a recorded matching shot', () => {
  for (const event of [
    { ...shot, end_x: undefined },
    { ...shot, x: NaN },
    { ...shot, end_y: 101 },
    { ...shot, type: 'recovery' },
  ])
    assert.equal(renderToStaticMarkup(React.createElement(PitchVector, { event })), '');
  const goal = {
    ...shot,
    event_id: 'g',
    type: 'goal',
    sequence: 2,
    match_second: 11,
    x: 0,
    end_x: null,
    end_y: null,
    related_event_id: 's',
  };
  assert.equal(vectorEvent(goal, []), null);
  assert.equal(vectorEvent(goal, [{ ...shot, player_id: 'other' }]), null);
  assert.equal(vectorEvent(goal, [{ ...shot, sequence: 3 }]), null);
  assert.equal(vectorEvent(goal, [shot]), shot);
  const html = renderToStaticMarkup(
    React.createElement(PitchVector, { event: goal, events: [shot] }),
  );
  assert.match(html, /Recorded shot linked to goal/);
  assert.match(html, /x1="25.44"/);
});

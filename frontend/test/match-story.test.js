import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';

// Render the actual shared JSX component, including its evidence drawer.
const bundle = await build({
  entryPoints: ['src/components/MatchStoryBriefing.jsx'],
  bundle: true,
  write: false,
  platform: 'node',
  format: 'esm',
  external: ['react'],
});
const source = bundle.outputFiles[0].text.replaceAll(
  'from "react"',
  `from ${JSON.stringify(import.meta.resolve('react'))}`,
);
const { MatchStoryBriefing } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);
const briefing = {
  headline: 'Newcastle led twice. Palace have answered twice.',
  scoreline: 'Palace 2–2 Newcastle',
  clock: '75:30',
  sections: [
    { title: 'The score story', text: 'Palace have pulled level.' },
    { title: 'Recent action', text: 'Six shots total, three each.' },
    { title: 'The clock', text: '14:30 until 90 minutes, plus added time.' },
  ],
  evidence_event_ids: ['goal1'],
  trajectory: {
    transitions: [
      { sequence: 1, match_second: 4511, after: { home: 2, away: 2 }, type: 'equalization' },
    ],
  },
};

test('shared card renders score story, activity and clock with collapsed evidence', () => {
  const html = renderToStaticMarkup(React.createElement(MatchStoryBriefing, { briefing }));
  for (const text of [
    'Newcastle led twice',
    'The score story',
    'Recent action',
    'The clock',
    '75:11',
    '2–2',
    'goal1',
  ])
    assert.ok(html.includes(text));
  assert.ok(html.includes('<details>'));
  assert.ok(!html.includes('<details open'));
});

test('shared card escapes feed names and safely handles absent briefing', () => {
  const html = renderToStaticMarkup(
    React.createElement(MatchStoryBriefing, {
      briefing: { ...briefing, headline: '<script>alert(1)</script>' },
    }),
  );
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.equal(
    renderToStaticMarkup(React.createElement(MatchStoryBriefing, { briefing: null })),
    '',
  );
});

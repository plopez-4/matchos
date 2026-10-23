import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';
import rosterMetadata from '../../backend/app/data/players_2026.json' with { type: 'json' };

const bundle = await build({
  entryPoints: {
    evidence: 'src/components/EvidenceList.jsx',
  },
  bundle: true,
  write: false,
  outdir: 'unused',
  platform: 'node',
  format: 'esm',
  external: ['react', 'react-dom'],
});
async function component(file) {
  const source = bundle.outputFiles
    .find((f) => f.path.endsWith(file))
    .text.replaceAll('from "react-dom"', `from ${JSON.stringify(import.meta.resolve('react-dom'))}`)
    .replaceAll('from "react"', `from ${JSON.stringify(import.meta.resolve('react'))}`);
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
}
const { EvidenceList } = await component('evidence.js');

test('evidence displays actual shirt numbers, not the synthetic actor slot as a jersey', () => {
  const html = renderToStaticMarkup(
    React.createElement(EvidenceList, {
      evidenceIds: ['pass'],
      events: [
        {
          event_id: 'pass',
          match_second: 100,
          team_id: 'home',
          type: 'pass',
          player_id: 'home-7',
          player_name: 'Enzo Fernandez',
          player_shirt_number: 17,
          player_position: 'MID',
          recipient_player_id: 'home-9',
          recipient_player_name: 'Phil Foden',
          recipient_player_shirt_number: 47,
          roster_version: rosterMetadata.version,
        },
      ],
    }),
  );
  assert.ok(html.includes('Enzo Fernandez') && html.includes('#17'));
  assert.ok(html.includes('Phil Foden') && html.includes('#47'));
  assert.ok(!html.includes('#7<'));
  assert.ok(html.includes('Synthetic action'));
  assert.ok(!html.includes('Assist'));
});

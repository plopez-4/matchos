import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';

const bundle = await build({
  entryPoints: ['src/components/NarratorControls.jsx'],
  bundle: true,
  write: false,
  platform: 'node',
  format: 'esm',
  external: ['react', 'react-dom'],
});
const source = bundle.outputFiles[0].text
  .replaceAll('from "react"', `from ${JSON.stringify(import.meta.resolve('react'))}`)
  .replaceAll('from "react-dom"', `from ${JSON.stringify(import.meta.resolve('react-dom'))}`);
const { NarratorControls } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);

test('both narrator layouts expose a separate bilingual listening speed control', () => {
  for (const compact of [true, false]) {
    for (const language of ['en', 'es']) {
      const html = renderToStaticMarkup(
        React.createElement(NarratorControls, {
          compact,
          language,
          story: {
            spoken_recap: { en: 'Recorded recap.', es: 'Resumen registrado.' },
            snapshot: { match_id: 'test' },
          },
        }),
      );
      assert.ok(html.includes(language === 'es' ? 'Velocidad de narración' : 'Narration speed'));
      assert.match(html, /<option value="1" selected="">1× · Normal<\/option>/);
      assert.ok(html.includes(language === 'es' ? '0,75× · Más lento' : '0.75× · Slower'));
      assert.ok(html.includes(language === 'es' ? 'Voz del narrador' : 'Narrator voice'));
      assert.equal((html.match(/value="0.75"/g) ?? []).length, 1);
    }
  }
});

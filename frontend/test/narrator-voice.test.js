import test from 'node:test';
import assert from 'node:assert/strict';
import { narratorVoice } from '../src/utils/narratorVoice.js';
import { localVoice } from '../src/utils/speechRecap.js';

test('automatic narration uses Azure even when this computer has no Spanish voice', () => {
  assert.equal(localVoice([{ lang: 'en-US', localService: true }], 'es'), null);
  assert.equal(narratorVoice('auto', true), 'matchday');
  assert.equal(narratorVoice('auto', false), 'device');
});

test('connecting Azure preserves an explicitly chosen voice', () => {
  assert.equal(narratorVoice('device', true), 'device');
  assert.equal(narratorVoice('warm', true), 'warm');
  assert.equal(narratorVoice('matchday', false), 'matchday');
});

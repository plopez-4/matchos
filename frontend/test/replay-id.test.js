import test from 'node:test';
import assert from 'node:assert/strict';
import { replayId } from '../src/utils/replayId.js';
test('phone HTTP replay IDs need no secure-context randomUUID and remain bounded', () => {
  const source = {
    getRandomValues(bytes) {
      bytes.fill(171);
      return bytes;
    },
  };
  assert.equal(replayId('test-v4', source), `test-v4-${'ab'.repeat(16)}`);
  const ids = Array.from({ length: 100 }, () => replayId());
  assert.equal(new Set(ids).size, 100);
  assert.ok(ids.every((id) => /^[a-zA-Z0-9_-]{1,60}$/.test(id)));
});

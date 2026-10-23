import test from 'node:test';
import assert from 'node:assert/strict';
import { createAudioPlayback } from '../src/utils/audioPlayback.js';
import { createSpeechRecap } from '../src/utils/speechRecap.js';

function player() {
  const states = [],
    instances = [],
    revoked = [];
  class Audio {
    constructor(url) {
      this.url = url;
      instances.push(this);
    }
    async play() {}
    pause() {
      this.paused = true;
    }
  }
  const playback = createAudioPlayback({
    AudioConstructor: Audio,
    urlApi: { createObjectURL: () => 'blob:audio', revokeObjectURL: (url) => revoked.push(url) },
    onState: (state, message) => states.push({ state, message }),
  });
  return { playback, states, instances, revoked };
}
test('cloud playback stops and releases its URL on completion', async () => {
  const p = player();
  assert.equal(await p.playback.play(async () => ({ blob: 'audio' })), true);
  assert.equal(p.states.at(-1).state, 'speaking');
  p.instances[0].onended();
  assert.equal(p.states.at(-1).state, 'idle');
  assert.deepEqual(p.revoked, ['blob:audio']);
});
test('aborting a pending cloud request never starts late audio', async () => {
  const p = player();
  let resolve, signal;
  const pending = p.playback.play((options) => {
    signal = options.signal;
    return new Promise((done) => (resolve = done));
  });
  p.playback.stop();
  assert.ok(signal.aborted);
  resolve({ blob: 'audio' });
  assert.equal(await pending, false);
  assert.equal(p.instances.length, 0);
});
test('device and cloud audio share one owner and do not overlap', async () => {
  const p = player();
  let cancelled = 0;
  class Utterance {
    constructor(text) {
      this.text = text;
    }
  }
  const native = createSpeechRecap({
    synth: {
      getVoices: () => [{ localService: true, lang: 'en-US' }],
      speak() {},
      cancel() {
        cancelled++;
      },
    },
    Utterance,
  });
  native.listen('Snapshot', 'en');
  await p.playback.play(async () => ({ blob: 'audio' }));
  assert.equal(cancelled, 1);
  native.listen('New snapshot', 'en');
  assert.ok(p.instances[0].paused);
  assert.equal(p.revoked.length, 1);
  native.stop();
});
test('cloud errors do not silently switch to the basic device reader', async () => {
  const p = player();
  assert.equal(
    await p.playback.play(async () => {
      throw new Error('Speech resource unavailable');
    }),
    false,
  );
  assert.equal(p.states.at(-1).state, 'error');
  assert.equal(p.states.at(-1).message, 'Speech resource unavailable');
  assert.equal(p.instances.length, 0);
});

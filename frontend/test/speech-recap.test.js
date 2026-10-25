import test from 'node:test';
import assert from 'node:assert/strict';
import { createSpeechRecap, localVoice, recapText } from '../src/utils/speechRecap.js';

test('device voice uses the server recap in the selected language, preserving older responses', () => {
  const story = {
    headline: 'Headline',
    scoreline: '2–2',
    clock: '75:30',
    sections: [{ text: 'Detailed evidence' }],
    spoken_recap: { en: 'Palace have answered twice.', es: 'Palace respondió dos veces.' },
  };
  assert.equal(recapText(story, 'es'), story.spoken_recap.es);
  assert.equal(recapText(story, 'en'), story.spoken_recap.en);
  const { spoken_recap, ...older } = story;
  assert.equal(recapText(older, 'en'), 'Headline. 2–2. 75:30. Detailed evidence');
  assert.equal(recapText(null, 'en'), '');
});

const en = { lang: 'en-US', localService: true, default: true };
const es = { lang: 'es-ES', localService: true };
function fixture(voices = [en, es]) {
  const spoken = [],
    states = [];
  let cancels = 0;
  const synth = {
    getVoices: () => voices,
    speak: (utterance) => spoken.push(utterance),
    cancel: () => cancels++,
  };
  class Utterance {
    constructor(text) {
      this.text = text;
    }
  }
  const controller = createSpeechRecap({
    synth,
    Utterance,
    onState: (state) => states.push(state),
  });
  return { controller, synth, spoken, states, cancels: () => cancels };
}
test('audio selects matching local voices only, never a remote or wrong-language fallback', () => {
  assert.equal(localVoice([{ lang: 'es-MX', localService: false }, en], 'es'), null);
  const f = fixture([{ lang: 'en-US', localService: false }]);
  assert.equal(f.controller.listen('Facts', 'en'), false);
  assert.equal(f.spoken.length, 0);
  assert.equal(f.states.at(-1), 'unavailable');
});
test('speech reads the supplied snapshot, sets its language, and supports completion and stop', () => {
  const f = fixture();
  assert.equal(f.controller.listen('Palace empató. 2–2.', 'es'), true);
  assert.equal(f.spoken[0].text, 'Palace empató. 2–2.');
  assert.equal(f.spoken[0].voice, es);
  assert.equal(f.spoken[0].lang, 'es-ES');
  f.spoken[0].onend();
  assert.equal(f.states.at(-1), 'idle');
  f.controller.listen('Second snapshot', 'en');
  f.controller.stop();
  assert.equal(f.cancels(), 1);
  assert.equal(f.spoken[1].onend, null);
});
test('device voice pronounces English match clocks ending in :00 as minutes', () => {
  const f = fixture();
  f.controller.listen('Goal at 15:00. At 20:00 minutes, United led. Window 10:00–20:00. Kickoff at 1:00.', 'en');
  assert.equal(f.spoken[0].text, 'Goal at 15 minutes. At 20 minutes, United led. Window 10 minutes–20 minutes. Kickoff at 1 minute.');
});
test('two story cards cannot queue overlapping recaps; old cleanup cannot cancel the new one', () => {
  const a = fixture(),
    b = fixture();
  a.controller.listen('First', 'en');
  b.controller.listen('Second', 'en');
  assert.equal(a.cancels(), 1);
  assert.equal(a.states.at(-1), 'idle');
  a.controller.stop();
  assert.equal(b.cancels(), 0);
  b.controller.stop();
});
test('speech failure resets the controller instead of leaving a permanent Stop state', () => {
  const f = fixture();
  f.synth.speak = () => {
    throw new Error('device failure');
  };
  assert.equal(f.controller.listen('Facts', 'en'), false);
  assert.equal(f.states.at(-1), 'error');
  f.controller.stop();
  assert.equal(f.cancels(), 0);
});

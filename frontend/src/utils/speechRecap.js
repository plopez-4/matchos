import { claimAudio, ownsAudio, releaseAudio } from './audioOwner.js';

export function recapText(story, language) {
  if (!story) return '';
  return (
    story.spoken_recap?.[language] ??
    [story.headline, story.scoreline, story.clock, ...story.sections.map((s) => s.text)].join('. ')
  );
}

export function localVoice(voices, language) {
  return (
    voices
      .filter(
        (voice) =>
          voice.localService === true && voice.lang.toLowerCase().split('-')[0] === language,
      )
      .sort((a, b) => Number(b.default) - Number(a.default))[0] ?? null
  );
}

export function createSpeechRecap({ synth, Utterance, onState = () => {} }) {
  let current;
  function stop() {
    if (!current) return;
    current.onend = current.onerror = null;
    current = null;
    if (ownsAudio(stop)) {
      releaseAudio(stop);
      synth.cancel();
    }
    onState('idle');
  }
  return {
    stop,
    listen(text, language) {
      const voice = localVoice(synth.getVoices(), language);
      if (!voice) {
        onState('unavailable');
        return false;
      }
      claimAudio(stop);
      const utterance = new Utterance(text);
      utterance.voice = voice;
      utterance.lang = voice.lang;
      current = utterance;
      const finish = (state) => {
        if (current !== utterance) return;
        current = null;
        releaseAudio(stop);
        onState(state);
      };
      utterance.onend = () => finish('idle');
      utterance.onerror = () => finish('error');
      try {
        onState('speaking');
        synth.speak(utterance);
        return true;
      } catch {
        finish('error');
        return false;
      }
    },
  };
}

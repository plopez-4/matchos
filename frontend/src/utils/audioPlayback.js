import { claimAudio, releaseAudio } from './audioOwner.js';
import { narrationRate } from './narratorVoice.js';

export function createAudioPlayback({ AudioConstructor, urlApi, onState = () => {} }) {
  let current;
  let rate = 1;
  function clear(state = 'idle', message = '') {
    const job = current;
    current = null;
    if (!job) return;
    job.abort.abort();
    if (job.audio) {
      job.audio.onended = job.audio.onerror = null;
      job.audio.pause();
    }
    if (job.url) urlApi.revokeObjectURL(job.url);
    releaseAudio(stop);
    onState(state, message);
  }
  function stop() {
    clear();
  }
  return {
    stop,
    setRate(value) {
      rate = narrationRate(value);
      if (current?.audio) current.audio.playbackRate = rate;
    },
    async play(fetchClip) {
      claimAudio(stop);
      const job = { abort: new AbortController() };
      current = job;
      onState('loading');
      try {
        const clip = await fetchClip({ signal: job.abort.signal });
        if (current !== job || job.abort.signal.aborted) return false;
        job.url = urlApi.createObjectURL(clip.blob);
        job.audio = new AudioConstructor(job.url);
        job.audio.preservesPitch = true;
        job.audio.playbackRate = rate;
        job.audio.onended = () => {
          if (current === job) clear();
        };
        job.audio.onerror = () => {
          if (current === job) clear('error', 'Audio could not be played');
        };
        await job.audio.play();
        if (current !== job) return false;
        onState('speaking');
        return true;
      } catch (error) {
        if (current === job) clear('error', error.message || 'Narration could not be played');
        return false;
      }
    },
  };
}

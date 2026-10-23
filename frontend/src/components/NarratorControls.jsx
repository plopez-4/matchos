import React, { useEffect, useRef, useState } from 'react';
import { createSpeechRecap, localVoice, recapText } from '../utils/speechRecap';
import { createAudioPlayback } from '../utils/audioPlayback';
import { narratorVoice } from '../utils/narratorVoice';
import { fetchNarrationStatus, fetchNarration, auditionNarrator } from '../api';

export function NarratorControls({ story, language, compact = false, onListen }) {
  const [voice, setVoice] = useState(compact ? 'auto' : 'matchday');
  const [cloud, setCloud] = useState(false);
  const [local, setLocal] = useState(false);
  const [state, setState] = useState('idle');
  const [message, setMessage] = useState('');
  const [snapshotClock, setSnapshotClock] = useState('');
  const controls = useRef(null);
  const spanish = language === 'es';
  const text = recapText(story, language);
  const playbackVoice = narratorVoice(voice, cloud);
  useEffect(() => {
    let mounted = true;
    setState('idle');
    setMessage('');
    const onState = (next, error = '') => {
      if (mounted) {
        setState(next);
        setMessage(error);
      }
    };
    const audio = createAudioPlayback({
      AudioConstructor: window.Audio,
      urlApi: window.URL,
      onState,
    });
    const synth = window.speechSynthesis;
    const speech =
      synth && typeof window.SpeechSynthesisUtterance === 'function'
        ? createSpeechRecap({ synth, Utterance: window.SpeechSynthesisUtterance, onState })
        : null;
    const update = () => setLocal(Boolean(speech && localVoice(synth.getVoices(), language)));
    update();
    synth?.addEventListener('voiceschanged', update);
    fetchNarrationStatus().then((status) => {
      if (mounted) setCloud(Boolean(status.available && typeof window.Audio === 'function'));
    });
    controls.current = { audio, speech };
    return () => {
      mounted = false;
      audio.stop();
      speech?.stop();
      synth?.removeEventListener('voiceschanged', update);
      controls.current = null;
    };
  }, [playbackVoice, language, story?.snapshot?.match_id, text]);

  const active = state === 'loading' || state === 'speaking';
  const ready = playbackVoice === 'device' ? local : cloud && Boolean(story?.snapshot);
  async function refreshVoice() {
    const status = await fetchNarrationStatus({ refresh: true });
    setCloud(Boolean(status.available && typeof window.Audio === 'function'));
  }
  function stop() {
    controls.current?.audio.stop();
    controls.current?.speech?.stop();
  }
  function listen(audition = false) {
    if (active) {
      stop();
      return;
    }
    setSnapshotClock(audition ? '75:30' : story.clock);
    onListen?.();
    if (playbackVoice === 'device') {
      controls.current?.speech?.listen(text, language);
      return;
    }
    controls.current?.audio.play((options) =>
      audition
        ? auditionNarrator(language, playbackVoice, options)
        : fetchNarration(story.snapshot, language, playbackVoice, {
            ...options,
            narrativeId: story.narrative?.id,
            audience: story.audience ?? 'casual',
            selectedStoryIds: story.story_plan?.story_ids,
          }),
    );
  }
  const status =
    state === 'error'
      ? spanish
        ? 'No se pudo reproducir la narración. Inténtalo de nuevo o elige la voz del dispositivo.'
        : message || 'Narration could not be played'
      : active
        ? `${state === 'loading' ? (spanish ? 'Preparando narración' : 'Preparing narration') : spanish ? 'Leyendo instantánea' : 'Reading snapshot'} ${snapshotClock}`
        : playbackVoice === 'device'
          ? local
            ? spanish
              ? 'Voz básica del dispositivo'
              : 'Basic device voice'
            : spanish
              ? 'No hay una voz en español instalada. Elige la voz automática y conecta Azure Speech.'
              : 'No voice is installed for this language. Choose Automatic and connect Azure Speech.'
          : cloud
            ? spanish
              ? 'Narrador Azure · resumen mostrado'
              : 'Azure narrator · displayed recap'
            : spanish
              ? 'Azure Speech no está conectado en este servidor. La traducción del texto funciona por separado.'
              : 'Azure Speech is not connected on this server. Text translation works separately.';
  const choice = (
    <label className="narrator-choice">
      {spanish ? 'Voz' : 'Voice'}
      <select
        aria-label={spanish ? 'Voz del narrador' : 'Narrator voice'}
        value={voice}
        onChange={(event) => setVoice(event.target.value)}
      >
        {compact && (
          <option value="auto">
            {spanish ? 'Automática (Azure si está conectado)' : 'Automatic (Azure when connected)'}
          </option>
        )}
        <option value="device">{spanish ? 'Dispositivo (básica)' : 'Device voice (basic)'}</option>
        <option value="matchday">{spanish ? 'Narrador de partido' : 'Matchday narrator'}</option>
        <option value="warm">{spanish ? 'Narrador cercano' : 'Warm storyteller'}</option>
      </select>
    </label>
  );
  if (compact)
    return (
      <div className="focus-voice">
        <button type="button" disabled={!active && (!ready || !text)} onClick={() => listen()}>
          {active
            ? spanish
              ? '■ Detener'
              : '■ Stop'
            : spanish
              ? '🔊 Escuchar resumen'
              : '🔊 Listen to recap'}
        </button>
        <small role="status">{status}</small>
        <details>
          <summary>{spanish ? 'Opciones de voz' : 'Voice options'}</summary>
          {choice}
          {voice !== 'device' && (
            <button type="button" onClick={refreshVoice}>
              {spanish ? 'Comprobar conexión de voz' : 'Check voice connection'}
            </button>
          )}
        </details>
      </div>
    );
  return (
    <span className="listen-recap">
      <label className="narrator-choice">
        {spanish ? 'Voz' : 'Voice'}
        <select
          aria-label={spanish ? 'Voz del narrador' : 'Narrator voice'}
          value={voice}
          onChange={(event) => setVoice(event.target.value)}
        >
          <option value="matchday">{spanish ? 'Narrador de partido' : 'Matchday narrator'}</option>
          <option value="warm">{spanish ? 'Narrador cercano' : 'Warm storyteller'}</option>
          <option value="device">
            {spanish ? 'Dispositivo (básica)' : 'Device voice (basic)'}
          </option>
        </select>
      </label>
      <span className="narrator-actions">
        <button type="button" disabled={!active && (!ready || !text)} onClick={() => listen()}>
          {active ? (spanish ? '■ Detener' : '■ Stop') : spanish ? '🔊 Escuchar' : '🔊 Listen'}
        </button>
        {voice !== 'device' && (
          <button type="button" disabled={!cloud || active} onClick={() => listen(true)}>
            {spanish ? 'Probar voz' : 'Preview voice'}
          </button>
        )}
      </span>
      <small role="status">{status}</small>
      {!cloud && !active && (
        <button type="button" onClick={refreshVoice}>
          {spanish ? 'Comprobar conexión de voz' : 'Check voice connection'}
        </button>
      )}
    </span>
  );
}

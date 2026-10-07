import React, { useEffect, useRef, useState } from 'react';
import { fetchReplayScenario, ingestReplayEvent } from '../api';
import { playReplay } from '../utils/replay';

export function ReplayControls({ matchId, hasEvents, loading, autoStart, onNewMatch }) {
  const [events, setEvents] = useState(null);
  const [running, setRunning] = useState(autoStart);
  const [speed, setSpeed] = useState(1);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const cursor = useRef(0);

  useEffect(() => {
    const controller = new AbortController();
    fetchReplayScenario(matchId, { signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) setEvents(result);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(`Could not load replay: ${err.message}`);
          setRunning(false);
        }
      });
    return () => controller.abort();
  }, [matchId, attempt]);

  useEffect(() => {
    if (!running || !events) return;
    const controller = new AbortController();
    playReplay({
      events,
      startIndex: cursor.current,
      intervalMs: 3000 / speed,
      signal: controller.signal,
      ingest: ingestReplayEvent,
      onProgress: (count) => {
        cursor.current = count;
        setProgress(count);
      },
    })
      .then((finished) => {
        if (finished && !controller.signal.aborted) setRunning(false);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(`Replay stopped: ${err.message}. You can retry the remaining events.`);
          setRunning(false);
        }
      });
    return () => controller.abort();
  }, [running, events, speed]);

  const finished = events && progress === events.length;
  const start = () => {
    if ((hasEvents && progress === 0) || finished) return onNewMatch(true);
    setError('');
    if (!events) setAttempt((value) => value + 1);
    setRunning(true);
  };
  const state = finished ? 'Finished' : running ? 'Playing' : progress ? 'Paused' : 'Ready';

  return (
    <section className="dashboard-card replay-card" aria-label="Match replay controls">
      <div className="card-header">
        <div className="header-text-group">
          <h2 className="card-title">Play the match</h2>
          <p className="card-subtitle">
            A fictional ten-minute highlight reel. You control the pace.
          </p>
        </div>
        <span className="feature-pill">{state}</span>
      </div>
      <div className="replay-actions">
        <button
          type="button"
          className="btn-primary"
          disabled={loading && !running}
          onClick={running ? () => setRunning(false) : start}
        >
          {running
            ? 'Pause'
            : finished || (hasEvents && !progress)
              ? 'Start new replay'
              : progress
                ? 'Resume'
                : 'Start replay'}
        </button>
        <button type="button" className="replay-reset" onClick={() => onNewMatch(false)}>
          Reset
        </button>
        <label className="replay-speed">
          Speed
          <select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}>
            <option value={0.5}>0.5× · Slow</option>
            <option value={1}>1× · Normal</option>
            <option value={2}>2× · Fast</option>
            <option value={4}>4× · Quick</option>
          </select>
        </label>
      </div>
      <div className="replay-progress">
        <progress value={progress} max={events?.length || 30} aria-label="Replay progress" />
        <span>
          {progress} / {events?.length || 30} highlights
        </span>
      </div>
      <p className="card-subtitle">
        Normal speed delivers one event every three seconds. Keep this page open while playing.
        Reset opens a fresh match.
      </p>
      {error && (
        <p className="replay-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

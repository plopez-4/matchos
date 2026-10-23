import { DEMO_FIXTURES } from '../utils/scenarios';
import React, { useEffect, useRef, useState, useImperativeHandle } from 'react';
import { fetchReplayScenario, fetchReplayScenarios, ingestReplayEvent } from '../api';
import { playReplay } from '../utils/replay';

const DEFAULT_CATALOG = DEMO_FIXTURES;

export function ReplayControls({
  matchId,
  scenarioId = 'united-city-90',
  hasEvents,
  loading,
  autoStart,
  onNewMatch,
  onScenarioChange,
  compact = false,
  controlsRef,
  running: controlledRunning,
  onRunningChange,
  observedSequence = 0,
}) {
  const [catalog, setCatalog] = useState(DEFAULT_CATALOG);
  const [events, setEvents] = useState(null);
  const [localRunning, setLocalRunning] = useState(autoStart);
  const running = controlledRunning ?? localRunning;
  const setRunning = onRunningChange ?? setLocalRunning;
  const [speed, setSpeed] = useState(1);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const cursor = useRef(0);
  const activeReplay = useRef(null);
  const pendingAdvance = useRef(null);

  useImperativeHandle(controlsRef, () => ({
    async pause() {
      setRunning(false);
      activeReplay.current?.abort();
      // Let the one server write already sent finish before taking a recap snapshot.
      await pendingAdvance.current?.catch(() => {});
    },
    resume() {
      if (!finished) start();
    },
  }));

  useEffect(() => {
    if (events && observedSequence > cursor.current) {
      cursor.current = Math.min(observedSequence, events.length);
      setProgress(cursor.current);
    }
  }, [events, observedSequence]);

  useEffect(() => {
    const controller = new AbortController();
    fetchReplayScenarios({ signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted && Array.isArray(data) && data.length > 0) {
          setCatalog(data);
        }
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchReplayScenario(matchId, scenarioId, { signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) setEvents(result);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(
            err.status === 403
              ? 'This replay is controlled by another session. You can watch it here or Reset to start your own.'
              : `Could not load replay: ${err.message}`,
          );
          setRunning(false);
        }
      });
    return () => controller.abort();
  }, [matchId, scenarioId, attempt]);

  useEffect(() => {
    if (!running || !events) return;
    const controller = new AbortController();
    activeReplay.current = controller;
    playReplay({
      events,
      startIndex: cursor.current,
      intervalMs: 3000 / speed,
      signal: controller.signal,
      ingest: (event) => {
        const pending = ingestReplayEvent(event).then((result) => {
          cursor.current = event.sequence;
          setProgress(event.sequence);
          return result;
        });
        pendingAdvance.current = pending;
        return pending.finally(() => {
          if (pendingAdvance.current === pending) pendingAdvance.current = null;
        });
      },
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

  const currentScenario =
    catalog.find((item) => item.id === scenarioId) || catalog[0] || DEFAULT_CATALOG[0];
  const maxEvents = events?.length || currentScenario.event_count || 30;
  const finished = events && progress === events.length;

  const start = () => {
    if ((hasEvents && progress === 0) || finished) return onNewMatch(true, scenarioId);
    setError('');
    if (!events) setAttempt((value) => value + 1);
    setRunning(true);
  };

  const handleSelectScenario = (e) => {
    const newId = e.target.value;
    if (newId === scenarioId) return;
    setRunning(false);
    if (onScenarioChange) {
      onScenarioChange(newId);
    } else {
      onNewMatch(false, newId);
    }
  };

  const state = finished ? 'Finished' : running ? 'Playing' : progress ? 'Paused' : 'Ready';

  const extraControls = (
    <>
      <button type="button" className="replay-reset" onClick={() => onNewMatch(false, scenarioId)}>
        Reset
      </button>
      <label className="replay-speed">
        Speed
        <select
          value={speed}
          onChange={(event) => setSpeed(Number(event.target.value))}
          aria-label="Replay speed"
        >
          <option value={0.5}>0.5× · Slow</option>
          <option value={1}>1× · Normal</option>
          <option value={2}>2× · Fast</option>
          <option value={4}>4× · Quick</option>
          <option value={20}>20× · Full match</option>
          <option value={80}>80× · Fast preview</option>
        </select>
      </label>
    </>
  );

  return (
    <section
      className={`dashboard-card replay-card ${compact ? 'replay-card-compact' : ''}`}
      aria-label="Match replay controls"
    >
      <div className="card-header">
        <div className="header-text-group">
          <h2 className="card-title">{compact ? 'Match playback' : 'Play the match'}</h2>
          <p className="card-subtitle scenario-description">
            {currentScenario.description ||
              'A fictional ten-minute highlight reel. You control the pace.'}
          </p>
        </div>
        <span className="feature-pill">{state}</span>
      </div>
      <div className="replay-actions">
        <label className="replay-scenario-picker" htmlFor="replay-scenario-select">
          <span className="picker-label">Scenario</span>
          <select
            id="replay-scenario-select"
            value={scenarioId}
            onChange={handleSelectScenario}
            aria-label="Select match scenario"
          >
            {catalog.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name}
                {!compact && ` (${sc.event_count} events)`}
              </option>
            ))}
          </select>
        </label>
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
        {compact ? (
          <details className="fan-demo-settings">
            <summary>Demo settings</summary>
            <div>{extraControls}</div>
          </details>
        ) : (
          extraControls
        )}
      </div>
      {!compact && (
        <div className="replay-progress">
          <progress value={progress} max={maxEvents} aria-label="Replay progress" />
          <span>
            {progress} / {maxEvents} events
          </span>
        </div>
      )}
      {!compact && (
        <p className="card-subtitle">
          Normal speed delivers one event every three seconds. Speed controls event delivery, not
          the match clock. Keep this page open while playing. Reset opens a fresh match.
        </p>
      )}
      {error && (
        <p className="replay-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

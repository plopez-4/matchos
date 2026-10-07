import React, { useEffect, useRef, useState } from 'react';
import { fetchReplayScenario, fetchReplayScenarios, ingestReplayEvent } from '../api';
import { playReplay } from '../utils/replay';

const DEFAULT_CATALOG = [
  {
    id: 'pressure-builds',
    name: 'Pressure Builds',
    description:
      'Repeated attacking sequences, progressive passing, and high defensive recoveries culminating in a breakthrough.',
    event_count: 33,
  },
  {
    id: 'comeback',
    name: 'The Comeback',
    description:
      'An early opening goal followed by sustained second-phase attacking momentum and an equalizer.',
    event_count: 34,
  },
  {
    id: 'quiet-match',
    name: 'Quiet Match',
    description:
      'Disciplined midfield circulation and defensive restraint with limited attacking openings.',
    event_count: 30,
  },
  {
    id: 'legacy-default',
    name: 'Legacy Fixture',
    description: 'Fictional ten-minute highlight reel with balanced phases and a decisive finish.',
    event_count: 30,
  },
];

export function ReplayControls({
  matchId,
  scenarioId = 'pressure-builds',
  hasEvents,
  loading,
  autoStart,
  onNewMatch,
  onScenarioChange,
}) {
  const [catalog, setCatalog] = useState(DEFAULT_CATALOG);
  const [events, setEvents] = useState(null);
  const [running, setRunning] = useState(autoStart);
  const [speed, setSpeed] = useState(1);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const cursor = useRef(0);

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
          setError(`Could not load replay: ${err.message}`);
          setRunning(false);
        }
      });
    return () => controller.abort();
  }, [matchId, scenarioId, attempt]);

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

  return (
    <section className="dashboard-card replay-card" aria-label="Match replay controls">
      <div className="card-header">
        <div className="header-text-group">
          <h2 className="card-title">Play the match</h2>
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
            disabled={running}
            aria-label="Select match scenario"
          >
            {catalog.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name} ({sc.event_count} events)
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
        <button
          type="button"
          className="replay-reset"
          onClick={() => onNewMatch(false, scenarioId)}
        >
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
          </select>
        </label>
      </div>
      <div className="replay-progress">
        <progress value={progress} max={maxEvents} aria-label="Replay progress" />
        <span>
          {progress} / {maxEvents} highlights
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

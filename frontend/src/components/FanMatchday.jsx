import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { FanMatch } from './FanMatch';
import { startMatchday, fetchMatchday, tickMatchday, releaseMatchday } from '../api';
import { DEMO_FIXTURES, resolveScenario } from '../utils/scenarios';
import { playMatchday, createReleaseRecovery, nextRadarNotice } from '../utils/matchday';
import { alertMoment } from '../utils/matchFocus';
import { formatMatchSecond as clock } from '../utils/formatters';
import { replayId } from '../utils/replayId';

const freshDay = () => replayId();

export function FanMatchday({ initialScenarioId }) {
  const [dayId, setDayId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('day');
    return requested && /^[a-zA-Z0-9_-]{1,60}$/.test(requested) ? requested : freshDay();
  });
  const [scenario, setScenario] = useState(resolveScenario(initialScenarioId));
  const [view, setView] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState(null);
  const [moment, setMoment] = useState(null);
  const [language, setLanguage] = useState('en');
  const latest = useRef(null);
  const active = useRef(null);
  const pending = useRef(null);
  const epoch = useRef(0);
  const dismissed = useRef(new Set());
  const cursors = useRef({});
  const release = useRef(createReleaseRecovery(releaseMatchday));
  const fixture = DEMO_FIXTURES.find((item) => item.id === scenario);
  const matchId = `${view?.matchday_id ?? dayId}-${fixture.role}`;
  if (!cursors.current[matchId]) cursors.current[matchId] = { current: 0 };
  const es = language === 'es';
  const selected = view?.matches.find((entry) => entry.role === fixture.role);
  const fixedTestVersion = /^test-v([1-4])-/.exec(dayId)?.[1];

  function accept(next) {
    latest.current = next;
    setView(next);
    setNotice((current) => nextRadarNotice(current, next, dismissed.current));
  }

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    (async () => {
      await release.current.retry({ signal: controller.signal });
      const next = await startMatchday(dayId, { signal: controller.signal });
      if (!controller.signal.aborted) {
        accept(next);
        if (next.matchday_id !== dayId) setDayId(next.matchday_id);
      }
    })()
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [dayId]);

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('day', view?.matchday_id ?? dayId);
    url.searchParams.set('scenario', scenario);
    url.searchParams.set('match', matchId);
    window.history.replaceState(null, '', url);
  }, [dayId, view?.matchday_id, scenario, matchId]);

  useEffect(() => {
    if (!playing || !latest.current) return;
    const controller = new AbortController();
    active.current = controller;
    (async () => {
      // Speed changes cannot start a second write before the previous tick settles.
      await pending.current?.catch(() => {});
      if (controller.signal.aborted) return;
      const done = await playMatchday({
        initialView: latest.current,
        intervalMs: 30000 / speed,
        signal: controller.signal,
        step: (id, tick) => {
          // Drain an already sent write on Pause, rather than cancelling its response.
          const write = tickMatchday(id, tick).then((next) => {
            accept(next);
            return next;
          });
          pending.current = write;
          return write.finally(() => {
            if (pending.current === write) pending.current = null;
          });
        },
        onView: () => {},
      });
      if (done && !controller.signal.aborted) setPlaying(false);
    })().catch((err) => {
      if (!controller.signal.aborted) {
        setError(err.message);
        setPlaying(false);
      }
    });
    return () => controller.abort();
  }, [playing, speed, dayId]);

  async function pause() {
    active.current?.abort();
    setPlaying(false);
    await pending.current?.catch(() => {});
    if (latest.current) {
      try {
        accept(await fetchMatchday(latest.current.matchday_id));
      } catch (err) {
        setError(err.message);
      }
    }
  }

  async function resume() {
    const token = epoch.current;
    if (!latest.current || latest.current.finished) return;
    await pending.current?.catch(() => {});
    // Recover the authoritative clock if a previous write's response was lost.
    try {
      const next = await fetchMatchday(latest.current.matchday_id);
      if (token !== epoch.current) return;
      accept(next);
      setError('');
      setPlaying(true);
    } catch (err) {
      setError(err.message);
    }
  }

  async function reset() {
    epoch.current++;
    setLoading(true);
    await pause();
    if (latest.current) release.current.queue(latest.current.matchday_id);
    latest.current = null;
    setView(null);
    setNotice(null);
    setMoment(null);
    dismissed.current.clear();
    cursors.current = {};
    setError('');
    setDayId(freshDay());
  }

  async function openNotice() {
    const target = notice;
    if (!target) return;
    await pause();
    const current = nextRadarNotice(target, latest.current, dismissed.current);
    if (!current) {
      setNotice(null);
      return;
    }
    const targetFixture = DEMO_FIXTURES.find((item) => item.role === current.entry.role);
    setMoment(alertMoment(current.entry));
    setScenario(targetFixture.id);
    dismissed.current.add(target.id);
    setNotice(null);
  }

  const controls = (
    <section
      className="dashboard-card replay-card replay-card-compact"
      aria-label="Match replay controls"
    >
      <div className="card-header">
        <div className="header-text-group">
          <h2 className="card-title">{es ? 'Partidos en paralelo' : 'Match playback'}</h2>
          <p className="card-subtitle">
            {es
              ? 'Los tres partidos avanzan juntos. Cambiar de partido conserva su progreso.'
              : 'All three matches run together. Switching keeps their progress.'}
          </p>
        </div>
        <span className="feature-pill">
          {clock(view?.clock_second ?? 0)} ·{' '}
          {view?.finished ? 'Full time' : playing ? 'Playing' : 'Paused'}
        </span>
      </div>
      <div className="replay-actions">
        <label className="replay-scenario-picker" htmlFor="fan-match-select">
          <span className="picker-label">{es ? 'Partido' : 'Match'}</span>
          <select
            id="fan-match-select"
            aria-label="Select match scenario"
            value={scenario}
            onChange={(event) => {
              setMoment(null);
              setScenario(event.target.value);
            }}
          >
            {DEMO_FIXTURES.map((item) => {
              const entry = view?.matches.find((match) => match.role === item.role);
              return (
                <option key={item.id} value={item.id}>
                  {item.name}
                  {entry
                    ? ` · ${entry.pulse.score.home}–${entry.pulse.score.away}${entry.pulse.eligible ? ' · Hot' : ''}`
                    : ''}
                </option>
              );
            })}
          </select>
        </label>
        <button
          className="btn-primary"
          disabled={loading || !view || view.finished}
          onClick={playing ? pause : resume}
        >
          {playing ? 'Pause' : view?.tick ? 'Resume' : 'Start replay'}
        </button>
        <button className="replay-reset" onClick={reset} disabled={loading}>
          {es ? 'Nueva jornada' : 'New matchday'}
        </button>
        <details className="fan-demo-settings">
          <summary>{es ? 'Ajustes de demostración' : 'Demo settings'}</summary>
          <div>
            <label className="replay-speed">
              {es ? 'Ritmo de demostración' : 'Demo pace'}
              <select
                aria-label={es ? 'Ritmo de demostración' : 'Demo pace'}
                value={speed}
                onChange={(event) => setSpeed(Number(event.target.value))}
              >
                <option value={20}>Normal</option>
                <option value={80}>{es ? 'Rápido' : 'Fast'}</option>
              </select>
            </label>
            <p>
              {es
                ? 'Cada nueva jornada elige una de cuatro versiones por partido. Los tres se pausan al pedir el resumen o escucharlo.'
                : 'Each new matchday picks one of four versions per fixture. Catch Me Up and Listen pause all three.'}
            </p>
          </div>
        </details>
        <p className="focus-caption">
          {es
            ? 'Repetición sintética acelerada · el reloj avanza en pasos de 30 segundos.'
            : 'Accelerated synthetic replay · match clock advances in 30-second steps.'}
        </p>
        {fixedTestVersion && (
          <p className="focus-caption" role="status">
            {es ? 'Prueba fija · versión' : 'Fixed test · version'}{' '}
            {selected?.variant_id ?? fixedTestVersion} ·{' '}
            <a href="/testing.html">{es ? 'Volver a las pruebas' : 'Back to test hub'}</a>
          </p>
        )}
      </div>
      {selected?.starting_lineups && (
        <details className="fan-demo-settings">
          <summary>
            {es ? 'Alineaciones iniciales · 11 contra 11' : 'Starting lineups · 11 v 11'}
          </summary>
          <p>
            {es
              ? 'Alineaciones ficticias para esta simulación.'
              : 'Fictional starting lineups for this simulation.'}
          </p>
          {['home', 'away'].map((side) => (
            <div key={side}>
              <strong>{selected[side]}</strong>
              <p>
                {selected.starting_lineups[side]
                  .map((player) => `#${player.player_shirt_number} ${player.player_name}`)
                  .join(' · ')}
              </p>
            </div>
          ))}
        </details>
      )}
      {error && (
        <p className="focus-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );

  return (
    <>
      <FanMatch
        key={matchId}
        matchId={matchId}
        scenarioId={scenario}
        initialMoment={moment}
        sharedPlayback={{
          dayId: view?.matchday_id ?? dayId,
          ready: Boolean(view),
          running: playing,
          pause,
          resume,
          controls,
          cursor: cursors.current[matchId],
          language,
          setLanguage,
        }}
      />
      {notice &&
        notice.match_id !== matchId &&
        createPortal(
          <aside className="radar-notice radar-toast" aria-label="Hot match notification">
            <button
              className="radar-dismiss"
              aria-label="Dismiss hot match notification"
              onClick={() => {
                dismissed.current.add(notice.id);
                setNotice(null);
              }}
            >
              ×
            </button>
            <div role="status">
              <span className="radar-eyebrow">
                {es ? 'En otro partido' : 'Elsewhere'}: {notice.entry.home} vs {notice.entry.away} ·{' '}
                {clock(view.clock_second)}
              </span>
              <strong>{notice.reason.headline}</strong>
              <p>
                {notice.entry.home} {notice.entry.pulse.score.home}–{notice.entry.pulse.score.away}{' '}
                {notice.entry.away}
              </p>
              <p>{notice.reason.text}</p>
            </div>
            <button className="btn-primary" onClick={openNotice}>
              {notice.reason.trigger === 'red_card'
                ? es
                  ? 'Ver detalles de la expulsión →'
                  : 'View sending-off details →'
                : ['equalizer', 'lead_reversal'].includes(notice.reason.trigger)
                  ? es
                    ? 'Repetir la jugada del gol →'
                    : 'Replay the goal build-up →'
                  : es
                    ? 'Repetir la jugada →'
                    : 'Replay the moment →'}
            </button>
            <small className="recorded-replay-note">
              {notice.reason.trigger === 'red_card'
                ? es
                  ? 'Explicación del incidente ficticio registrado'
                  : 'Explanation of the recorded fictional incident'
                : es
                  ? 'Repetición esquemática a partir de acciones registradas'
                  : 'Schematic replay from recorded events'}
            </small>
          </aside>,
          document.body,
        )}
    </>
  );
}

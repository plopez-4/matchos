import React, { useEffect, useRef, useState } from 'react';
import {
  startMatchday,
  fetchMatchday,
  tickMatchday,
  releaseMatchday,
  postCatchUp,
  fetchMatchData,
} from '../api';
import { playMatchday, createReleaseRecovery } from '../utils/matchday';
import { MatchHeader } from './MatchHeader';
import { CatchUpPanel } from './CatchUpPanel';
import { EventTimeline } from './EventTimeline';

const clock = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
const freshId = () => `day-${crypto.randomUUID()}`;

export function Matchday() {
  const [dayId, setDayId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('day');
    return requested && /^[a-zA-Z0-9_-]{1,60}$/.test(requested) ? requested : freshId();
  });
  const [view, setView] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [starting, setStarting] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState(null);
  const [selected, setSelected] = useState(null);
  const [summary, setSummary] = useState(null);
  const [audience, setAudience] = useState('casual');
  const [busy, setBusy] = useState(false);
  const [briefError, setBriefError] = useState('');
  const [events, setEvents] = useState([]);
  const [highlight, setHighlight] = useState(null);
  const latest = useRef(null);
  const generation = useRef(0);
  const setupRequest = useRef(null);
  const briefRequest = useRef(null);
  const noticeTimer = useRef(null);
  const seenNotice = useRef(null);
  const releaseRecovery = useRef(createReleaseRecovery(releaseMatchday));

  function accept(next) {
    latest.current = next;
    setView(next);
  }

  useEffect(() => {
    const controller = new AbortController();
    fetchMatchday(dayId, { signal: controller.signal })
      .then((next) => {
        if (!controller.signal.aborted) accept(next);
      })
      .catch(() => {});
    return () => {
      controller.abort();
      generation.current++;
      setupRequest.current?.abort();
      setupRequest.current = null;
      briefRequest.current?.abort();
      clearTimeout(noticeTimer.current);
    };
  }, [dayId]);

  useEffect(() => {
    if (!playing || !latest.current) return;
    const controller = new AbortController();
    playMatchday({
      initialView: latest.current,
      intervalMs: 1000 / speed,
      signal: controller.signal,
      step: tickMatchday,
      onView: accept,
    })
      .then((done) => {
        if (done && !controller.signal.aborted) setPlaying(false);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(err.message);
          setPlaying(false);
        }
      });
    return () => controller.abort();
  }, [playing, speed, dayId]);

  useEffect(() => {
    if (view?.notification && view.notification.id !== seenNotice.current) {
      seenNotice.current = view.notification.id;
      setNotice(view.notification);
      clearTimeout(noticeTimer.current);
      noticeTimer.current = setTimeout(() => setNotice(null), 8000);
    } else {
      setNotice((current) =>
        current?.match_id === view?.recommendation?.match_id ? current : null,
      );
    }
  }, [view?.tick]);

  useEffect(() => {
    if (!selected) return;
    const controller = new AbortController();
    fetchMatchData(selected, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setEvents(data.events);
      })
      .catch(() => {});
    return () => controller.abort();
  }, [selected, view?.tick]);

  async function begin() {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (latest.current) {
      setError('');
      setPlaying(true);
      return;
    }
    const controller = new AbortController();
    setupRequest.current = controller;
    setStarting(true);
    setError('');
    try {
      await releaseRecovery.current.retry({ signal: controller.signal });
      if (controller.signal.aborted) return;
      const next = await startMatchday(dayId, { signal: controller.signal });
      if (controller.signal.aborted) return;
      accept(next);
      setPlaying(true);
      const url = new URL(window.location.href);
      url.searchParams.set('day', dayId);
      window.history.replaceState(null, '', url);
    } catch (err) {
      if (!controller.signal.aborted) setError(err.message);
    } finally {
      if (!controller.signal.aborted) setStarting(false);
    }
  }

  async function reset() {
    setPlaying(false);
    setupRequest.current?.abort();
    briefRequest.current?.abort();
    generation.current++;
    setStarting(true);
    const controller = new AbortController();
    setupRequest.current = controller;
    let warning = '';
    try {
      if (latest.current) releaseRecovery.current.queue(dayId);
      await releaseRecovery.current.retry({ signal: controller.signal });
    } catch (err) {
      warning =
        'The old replay could not be released. Start matchday will retry cleanup before creating a new replay.';
    }
    // Navigation must not be changed by an obsolete reset request.
    if (setupRequest.current !== controller) return;
    const id = freshId();
    latest.current = null;
    setView(null);
    setSelected(null);
    setSummary(null);
    seenNotice.current = null;
    clearTimeout(noticeTimer.current);
    setEvents([]);
    setNotice(null);
    setHighlight(null);
    setBusy(false);
    setBriefError('');
    setError(warning);
    setStarting(false);
    setDayId(id);
    const url = new URL(window.location.href);
    url.searchParams.set('day', id);
    window.history.replaceState(null, '', url);
  }

  async function catchUp(mid = selected, fromStart = false) {
    if (!mid) return;
    briefRequest.current?.abort();
    const controller = new AbortController();
    briefRequest.current = controller;
    const currentGen = ++generation.current;
    setBusy(true);
    setBriefError('');
    try {
      const result = await postCatchUp(
        mid,
        { audience, since_sequence: fromStart ? 0 : (summary?.through_sequence ?? 0) },
        { signal: controller.signal },
      );
      if (!controller.signal.aborted && currentGen === generation.current) setSummary(result);
    } catch (err) {
      if (!controller.signal.aborted && currentGen === generation.current)
        setBriefError(err.message);
    } finally {
      if (currentGen === generation.current) setBusy(false);
    }
  }

  function follow(mid) {
    setSelected(mid);
    setSummary(null);
    setEvents([]);
    setHighlight(null);
    catchUp(mid, true);
  }

  const recommended = view?.recommendation;
  const followed = view?.matches.find((item) => item.match_id === selected);
  return (
    <div className="matchos-app">
      <MatchHeader status={error ? 'stale' : view ? 'connected' : 'empty'} error={error} />
      <main className="matchday-layout">
        <section className="dashboard-card matchday-intro">
          <span className="feature-pill">Synthetic matchday</span>
          <h1>Find the story beyond your fixture.</h1>
          <p>
            Three games. One shared clock. Match Radar highlights a developing story using recorded
            events.
          </p>
          <div className="replay-actions">
            <button className="btn-primary" onClick={begin} disabled={starting || view?.finished}>
              {starting
                ? 'Preparing…'
                : playing
                  ? 'Pause matchday'
                  : view
                    ? 'Resume matchday'
                    : 'Start matchday'}
            </button>
            <button className="replay-reset" onClick={reset} disabled={starting}>
              New matchday
            </button>
            <label>
              Speed{' '}
              <select
                aria-label="Matchday speed"
                value={speed}
                onChange={(event) => setSpeed(Number(event.target.value))}
              >
                <option value={1}>1×</option>
                <option value={2}>2×</option>
                <option value={4}>4×</option>
              </select>
            </label>
            <strong className="matchday-clock">
              {clock(view?.clock_second ?? 0)}{' '}
              {view?.finished ? '· Full time' : '· Shared match clock'}
            </strong>
          </div>
          <p className="card-subtitle">
            1× advances 30 match seconds per second. These are authored highlights, not real matches
            or live video.
          </p>
          {error && (
            <p role="alert" className="replay-error">
              {error}
            </p>
          )}
        </section>

        {notice && (
          <aside className="radar-notice" role="status">
            <strong>{notice.title}</strong>
            <p>{notice.reason}</p>
            <button className="btn-primary" onClick={() => follow(notice.match_id)}>
              Follow & catch me up
            </button>
          </aside>
        )}

        <section className="dashboard-card radar-card" aria-label="Match Radar">
          <div className="card-header">
            <div>
              <h2>Match Radar</h2>
              <p className="card-subtitle">
                A recommendation with a reason. Club popularity does not affect the ranking.
              </p>
            </div>
            <span className="feature-pill">Observed activity</span>
          </div>
          {recommended ? (
            <>
              <h3>
                Heating up: {recommended.home} vs {recommended.away}
              </h3>
              <p>{recommended.pulse.reason}</p>
              <p>
                {recommended.pulse.score.home}–{recommended.pulse.score.away} · Radar signal{' '}
                {recommended.pulse.rating}/100
              </p>
              <button className="btn-primary" onClick={() => follow(recommended.match_id)}>
                Follow & catch me up
              </button>
              <details>
                <summary>Why this match?</summary>
                <p>
                  The signal combines a close score, shots from both teams, increased shot activity,
                  late-match timing and recent goals. It is not a probability of excitement.
                </p>
                <ul>
                  {Object.entries(recommended.pulse.components).map(([key, value]) => (
                    <li key={key}>
                      {key.replaceAll('_', ' ')}: {value}
                    </li>
                  ))}
                </ul>
                <p>Supporting recorded events:</p>
                <ul className="radar-evidence">
                  {recommended.pulse.evidence_events.map((event) => (
                    <li key={event.event_id}>
                      {clock(event.match_second)} · {event.team_name} · {event.type}{' '}
                      <small>{event.event_id}</small>
                    </li>
                  ))}
                </ul>
              </details>
            </>
          ) : (
            <div className="radar-quiet">
              <h3>
                {view?.finished
                  ? 'The matchday is complete.'
                  : 'No match needs an alert right now.'}
              </h3>
              <p>
                Radar waits for enough recent activity from both sides in a close contest. A quiet
                draw alone does not qualify.
              </p>
            </div>
          )}
        </section>

        <section className="matchday-games" aria-label="Concurrent matches">
          {(view?.matches ?? []).map((item) => (
            <article
              className={`dashboard-card matchday-game ${item.match_id === recommended?.match_id ? 'is-heating' : ''}`}
              key={item.match_id}
            >
              <span className="feature-pill">
                {item.role === 'featured' ? 'Featured fixture' : 'Elsewhere'}
              </span>
              <h3>
                {item.home} <span>{item.pulse.score.home}</span>
              </h3>
              <h3>
                {item.away} <span>{item.pulse.score.away}</span>
              </h3>
              <p>
                Last five minutes: {item.pulse.shots_last_five.home}–
                {item.pulse.shots_last_five.away} shots
              </p>
              <p className="card-subtitle">
                Radar signal: {item.pulse.rating}/100 ·{' '}
                {item.pulse.eligible ? 'Heating up' : view.finished ? 'Finished' : 'Monitoring'}
              </p>
              <button className="replay-reset" onClick={() => follow(item.match_id)}>
                Follow this match
              </button>
            </article>
          ))}
        </section>

        {followed && (
          <section className="matchday-follow" aria-label="Selected match">
            <h2>
              Following {followed.home} vs {followed.away}
            </h2>
            <CatchUpPanel
              summary={summary}
              busy={busy}
              error={briefError}
              selectedAudience={audience}
              onAudienceChange={setAudience}
              onCatchUp={() => catchUp()}
              events={events}
              onSelectEvent={setHighlight}
            />
            <EventTimeline
              events={events}
              highlightedEventId={highlight}
              onClearHighlight={() => setHighlight(null)}
            />
          </section>
        )}
        <footer className="dashboard-footer">
          <p>
            Rule-based Radar baseline · synthetic data · no standings claims or measured engagement
            uplift. Notifications stay inside this page.
          </p>
        </footer>
      </main>
    </div>
  );
}

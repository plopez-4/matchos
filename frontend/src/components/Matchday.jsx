import { DevelopmentInspector } from './DevelopmentInspector';
import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  startMatchday,
  fetchMatchday,
  tickMatchday,
  releaseMatchday,
  postCatchUp,
  fetchMatchData,
} from '../api';
import { playMatchday, createReleaseRecovery, discoveryReason } from '../utils/matchday';
import { alertMoment, featuredMoment, momentTitle, retainCatchUp } from '../utils/matchFocus';
import { PitchReplay } from './PitchReplay';
import { FocusedRecap } from './FocusedRecap';
import { clubByName } from '../utils/teams';
import { formatMatchSecond as clock } from '../utils/formatters';

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
  const [sessionMessage, setSessionMessage] = useState('');
  const [notice, setNotice] = useState(null);
  const [selected, setSelected] = useState(null);
  const [summary, setSummary] = useState(null);
  const [audience, setAudience] = useState('casual');
  const [language, setLanguage] = useState('en');
  const [busy, setBusy] = useState(false);
  const [briefError, setBriefError] = useState('');
  const [events, setEvents] = useState([]);
  const [eventsError, setEventsError] = useState('');
  const [momentId, setMomentId] = useState(null);
  const [pitchRequest, setPitchRequest] = useState(null);
  const latest = useRef(null);
  const selectedPanel = useRef(null);
  const switcher = useRef(null);
  const generation = useRef(0);
  const setupRequest = useRef(null);
  const briefRequest = useRef(null);
  const lastCatchUp = useRef({ matchId: null, sequence: 0 });
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
      .catch((err) => {
        if (!controller.signal.aborted && err.status !== 404) setError(err.message);
      });
    return () => {
      controller.abort();
      generation.current++;
      setupRequest.current?.abort();
      setupRequest.current = null;
      briefRequest.current?.abort();
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
    } else
      setNotice((current) =>
        current?.match_id === view?.recommendation?.match_id ? current : null,
      );
  }, [view?.tick]);

  useEffect(() => {
    if (!selected && view?.matches.length) follow(view.recommendation ?? view.matches[0], false);
  }, [view?.matchday_id, selected]);

  useEffect(() => {
    if (!selected) return;
    const controller = new AbortController();
    fetchMatchData(selected, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setEvents(data.events);
          setEventsError('');
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) setEventsError(err.message);
      });
    return () => controller.abort();
  }, [selected, view?.tick]);

  async function begin() {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (latest.current) {
      briefRequest.current?.abort();
      generation.current++;
      setBusy(false);
      setError('');
      setMomentId(null);
      setSummary(null);
      setBriefError('');
      setPitchRequest({ latest: true, nonce: Date.now() });
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
      setPlaying(!next.finished);
      const url = new URL(window.location.href);
      url.searchParams.set('day', next.matchday_id);
      window.history.replaceState(null, '', url);
      if (next.matchday_id !== dayId) {
        setSessionMessage(
          'Reopened your existing demo. Use New demo in Demo controls for a fresh match.',
        );
        setStarting(false);
        setDayId(next.matchday_id);
      }
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
    } catch {
      warning = 'The old replay could not be released. Start demo will retry cleanup.';
    }
    if (setupRequest.current !== controller) return;
    latest.current = null;
    setView(null);
    setSelected(null);
    setSummary(null);
    seenNotice.current = null;
    lastCatchUp.current = { matchId: null, sequence: 0 };
    setNotice(null);
    setEvents([]);
    setEventsError('');
    setMomentId(null);
    setPitchRequest(null);
    setBusy(false);
    setBriefError('');
    setError(warning);
    setSessionMessage('');
    setStarting(false);
    const id = freshId();
    setDayId(id);
    const url = new URL(window.location.href);
    url.searchParams.set('day', id);
    window.history.replaceState(null, '', url);
  }

  async function catchUp(mid = selected, fromStart = false, style = audience, sinceOverride) {
    if (!mid) return;
    setPlaying(false);
    briefRequest.current?.abort();
    const controller = new AbortController();
    briefRequest.current = controller;
    const currentGen = ++generation.current;
    setBusy(true);
    setBriefError('');
    try {
      const result = await postCatchUp(
        mid,
        {
          audience: style,
          since_sequence:
            sinceOverride ??
            (!fromStart && summary?.fan_briefing && summary.fan_briefing.audience !== style
              ? summary.fan_briefing.snapshot.since_sequence
              : !fromStart && lastCatchUp.current.matchId === mid
                ? lastCatchUp.current.sequence
                : 0),
        },
        { signal: controller.signal },
      );
      if (!controller.signal.aborted && currentGen === generation.current) {
        lastCatchUp.current = { matchId: mid, sequence: result.through_sequence };
        setSummary((previous) => retainCatchUp(previous, result));
        // A tick may commit just as Pause cancels its browser response. Sync the
        // displayed clock and evidence to the snapshot the recap actually used.
        const [feed, day] = await Promise.allSettled([
          fetchMatchData(mid, { signal: controller.signal }),
          fetchMatchday(dayId, { signal: controller.signal }),
        ]);
        if (!controller.signal.aborted && currentGen === generation.current) {
          if (feed.status === 'fulfilled') {
            setEvents(feed.value.events);
            setEventsError('');
          } else setEventsError(feed.reason.message);
          if (day.status === 'fulfilled') accept(day.value);
        }
      }
    } catch (err) {
      if (!controller.signal.aborted && currentGen === generation.current)
        setBriefError(err.message);
    } finally {
      if (currentGen === generation.current) setBusy(false);
    }
  }

  function replay(event) {
    if (!event) return;
    setPlaying(false);
    setMomentId(event.event_id);
    setPitchRequest({ id: event.event_id, nonce: Date.now() });
  }

  function follow(entry, focus = true) {
    if (entry.match_id !== selected) {
      setSelected(entry.match_id);
      setEvents([]);
      setEventsError('');
    }
    setSummary(null);
    setBriefError('');
    const moment = alertMoment(entry);
    setMomentId(moment?.event_id ?? null);
    setPitchRequest(
      moment ? { id: moment.event_id, nonce: Date.now() } : { latest: true, nonce: Date.now() },
    );
    // Opening a promised moment holds its score/context steady during the build-up.
    if (moment) setPlaying(false);
    if (switcher.current) switcher.current.open = false;
    setNotice(null);
    if (moment) catchUp(entry.match_id, true);
    else {
      briefRequest.current?.abort();
      generation.current++;
      setBusy(false);
    }
    if (focus) {
      selectedPanel.current?.scrollIntoView({ block: 'start', behavior: 'instant' });
      selectedPanel.current?.focus({ preventScroll: true });
    }
  }

  function returnToLatest() {
    briefRequest.current?.abort();
    generation.current++;
    setBusy(false);
    setMomentId(null);
    setSummary(null);
    setBriefError('');
    setPitchRequest({ latest: true, nonce: Date.now() });
    if (!view?.finished) {
      setError('');
      setPlaying(true);
    }
  }

  const entry = view?.matches.find((item) => item.match_id === selected);
  const recommended = view?.recommendation;
  const reason = discoveryReason(recommended, view?.clock_second);
  const moment = momentId
    ? (events.find((event) => event.event_id === momentId) ??
      entry?.pulse.evidence_events.find((event) => event.event_id === momentId))
    : null;
  const featured = featuredMoment(events);
  const briefing = summary?.fan_briefing ?? entry?.briefing;
  const es = language === 'es';

  return (
    <div className="focus-app">
      <header className="focus-topbar">
        <a className="focus-brand" href={view ? `/?day=${dayId}` : '/'}>
          Match<span>OS</span>
        </a>
        <span className="focus-demo-label">
          {es ? 'Vista de desarrollo' : 'Development dashboard'}
        </span>
        {view && (
          <details className="focus-switcher" ref={switcher}>
            <summary>{es ? 'Otros partidos' : 'Other matches'}</summary>
            <div className="focus-match-options">
              {view.matches.map((item) => (
                <button
                  key={item.match_id}
                  aria-label={`${item.home} ${item.pulse.score.home}–${item.pulse.score.away} ${item.away}`}
                  aria-pressed={item.match_id === selected}
                  onClick={() => follow(item)}
                >
                  <span>
                    {item.home} <b>{item.pulse.score.home}</b>
                  </span>
                  <span>
                    {item.away} <b>{item.pulse.score.away}</b>
                  </span>
                  {item.match_id === recommended?.match_id && (
                    <small>{es ? 'Merece la pena verlo' : 'Worth a look'}</small>
                  )}
                </button>
              ))}
            </div>
          </details>
        )}
      </header>

      <main className="focus-main" ref={selectedPanel} tabIndex={-1}>
        {sessionMessage && <p role="status">{sessionMessage}</p>}
        {!view && (
          <section className="focus-welcome">
            <span className="focus-eyebrow">The match you missed.</span>
            <h1>See how it happened.</h1>
            <p>Replay the build-up. Understand what changed. Rejoin the match.</p>
            <p className="focus-caption">
              Real club and player names, fictional match action. This is a practice demo.
            </p>
            <button className="btn-primary" onClick={begin} disabled={starting}>
              {starting ? 'Preparing the match…' : 'Start demo'}
            </button>
          </section>
        )}

        {entry && (
          <>
            <section className="focus-score" aria-label="Selected match score">
              <div className="focus-team">
                <i style={{ background: clubByName(entry.home)?.color ?? '#7dd3fc' }} />
                {entry.home}
              </div>
              <div className="focus-score-centre">
                <strong>
                  {entry.pulse.score.home}
                  <span>–</span>
                  {entry.pulse.score.away}
                </strong>
                <span>
                  {clock(view.clock_second)} ·{' '}
                  {view.finished
                    ? es
                      ? 'Final'
                      : 'Full time'
                    : playing
                      ? es
                        ? 'Partido en marcha'
                        : 'Match running'
                      : es
                        ? 'En pausa'
                        : 'Paused'}
                </span>
              </div>
              <div className="focus-team focus-team-away">
                <i style={{ background: clubByName(entry.away)?.color ?? '#fff' }} />
                {entry.away}
              </div>
            </section>

            <div className="focus-review-state" role="status">
              <span>
                {playing
                  ? es
                    ? 'Siguiendo la acción más reciente.'
                    : 'Following the latest action.'
                  : es
                    ? `Revisando la acción hasta ${clock(view.clock_second)}.`
                    : `Reviewing action up to ${clock(view.clock_second)}.`}
                {!playing && !view.finished && (
                  <small>
                    {es
                      ? 'El partido está en pausa mientras repasas lo ocurrido.'
                      : 'The match is paused while you look back.'}
                  </small>
                )}
              </span>
              {!playing && (
                <button className="btn-primary" onClick={returnToLatest}>
                  {es
                    ? view.finished
                      ? 'Ver el final'
                      : 'Continuar partido'
                    : view.finished
                      ? 'Back to final action'
                      : 'Continue match'}
                </button>
              )}
            </div>

            <section className="focus-moment-heading" aria-label="Featured match moment">
              <div>
                <span className="focus-eyebrow">
                  {moment
                    ? `${moment.type === 'goal' ? 'Goal' : 'Chance'} · ${clock(moment.match_second)}`
                    : view.finished
                      ? 'The final story'
                      : 'On the pitch'}
                </span>
                <h1>
                  {view.finished && !moment ? 'How it ended.' : momentTitle(moment, entry.briefing)}
                </h1>
              </div>
              {featured && (
                <button className="btn-primary" onClick={() => replay(moment ?? featured)}>
                  {(moment ?? featured).type === 'goal'
                    ? es
                      ? 'Repetir gol'
                      : 'Replay goal'
                    : es
                      ? 'Repetir ocasión'
                      : 'Replay chance'}{' '}
                  <span aria-hidden="true">↗</span>
                </button>
              )}
            </section>

            {eventsError && (
              <p className="focus-error" role="alert">
                The pitch could not update: {eventsError}
              </p>
            )}
            <PitchReplay
              key={selected}
              compact
              language={language}
              events={events}
              request={pitchRequest}
              home={entry.home}
              away={entry.away}
              onMomentSelect={(event) => {
                setPlaying(false);
                setMomentId(event.event_id);
              }}
              onLatest={returnToLatest}
              showContinue={false}
            />
            <FocusedRecap
              briefing={briefing}
              summary={summary}
              events={events}
              busy={busy}
              error={briefError}
              audience={audience}
              language={language}
              onLanguageChange={setLanguage}
              onListen={() => setPlaying(false)}
              onAudienceChange={(style) => {
                setAudience(style);
                catchUp(selected, false, style, briefing?.snapshot?.since_sequence ?? 0);
              }}
              onCatchUp={() => catchUp()}
            />
          </>
        )}
        {view && !entry && <p role="status">Opening the match…</p>}
        {error && (
          <p className="focus-error" role="alert">
            {error}
          </p>
        )}

        {(new URLSearchParams(window.location.search).get('match') || selected) && (
          <DevelopmentInspector
            matchId={new URLSearchParams(window.location.search).get('match') || selected}
          />
        )}
        <details className="focus-demo-controls">
          <summary>Demo controls</summary>
          <div>
            {view && (
              <button className="replay-reset" onClick={begin} disabled={starting || view.finished}>
                {playing
                  ? es
                    ? 'Pausar partido'
                    : 'Pause match'
                  : es
                    ? 'Continuar partido'
                    : 'Continue match'}
              </button>
            )}
            <label>
              Match speed{' '}
              <select
                aria-label="Matchday speed"
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
              >
                <option value={1}>1×</option>
                <option value={2}>2×</option>
                <option value={4}>4×</option>
              </select>
            </label>
            <button className="replay-reset" onClick={reset} disabled={starting}>
              New demo
            </button>
            <a href="/">Main MatchOS page</a>
            <p>
              Fictional matches and recorded ball paths, not live video or player tracking. 1×
              advances 30 match seconds per second.
            </p>
          </div>
        </details>
      </main>
      <footer className="focus-footer">
        MatchOS ·{' '}
        {es
          ? '¿Te perdiste la acción? Mira cómo ocurrió.'
          : 'Missed the action? See how it happened.'}
        <br />
        Independent hackathon prototype · Fictional match action.
      </footer>

      {notice &&
        notice.match_id === recommended?.match_id &&
        reason &&
        createPortal(
          <aside className="radar-notice radar-toast" aria-label="Match Radar notification">
            <button
              className="radar-dismiss"
              aria-label="Dismiss Radar notification"
              onClick={() => setNotice(null)}
            >
              ×
            </button>
            <div role="status">
              <span className="radar-eyebrow">
                {recommended.home} · {recommended.away}
              </span>
              <strong>{reason.headline}</strong>
            </div>
            <button className="btn-primary" onClick={() => follow(recommended)}>
              {['equalizer', 'lead_reversal'].includes(recommended.pulse.why_now?.trigger)
                ? 'See the goal →'
                : 'See the moment →'}
            </button>
          </aside>,
          document.body,
        )}
    </div>
  );
}

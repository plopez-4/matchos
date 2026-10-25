import React, { useCallback, useEffect, useReducer, useRef, useState } from 'react';
import { useMatchData } from '../hooks/useMatchData';
import { catchUpReducer, initialCatchUpState } from '../utils/catchUpState';
import { featuredMoment, retainCatchUp } from '../utils/matchFocus';
import { teamsForScenario, variablesForTeams } from '../utils/teams';
import { formatMatchSecond } from '../utils/formatters';
import { postCatchUp } from '../api';
import { MatchHeader } from './MatchHeader';
import { Scoreboard } from './Scoreboard';
import { ReplayControls } from './ReplayControls';
import { PitchReplay } from './PitchReplay';
import { FocusedRecap } from './FocusedRecap';

export function FanMatch({
  matchId,
  scenarioId,
  autoStart,
  onNewMatch,
  onScenarioChange,
  sharedPlayback,
  initialMoment,
}) {
  const [result, dispatch] = useReducer(catchUpReducer, initialCatchUpState);
  const { summary, busy, error } = result;
  const [audience, setAudience] = useState('casual');
  const [localLanguage, setLocalLanguage] = useState('en');
  const language = sharedPlayback?.language ?? localLanguage;
  const setLanguage = sharedPlayback?.setLanguage ?? setLocalLanguage;
  const [running, setRunning] = useState(autoStart);
  const [reviewing, setReviewing] = useState(Boolean(initialMoment));
  const [pitchRequest, setPitchRequest] = useState(
    initialMoment ? { id: initialMoment.event_id, nonce: Date.now() } : null,
  );
  useEffect(() => {
    if (initialMoment) {
      setReviewing(true);
      setPitchRequest({ id: initialMoment.event_id, nonce: Date.now() });
    }
  }, [initialMoment]);
  const playback = useRef(null);
  const request = useRef(null);
  const generation = useRef(0);
  const localCursor = useRef(0);
  const cursor = sharedPlayback?.cursor ?? localCursor;
  const es = language === 'es';
  const reset = useCallback(() => {
    request.current?.abort();
    request.current = null;
    cursor.current = 0;
    setRunning(false);
    setReviewing(false);
    setPitchRequest(null);
    dispatch({ type: 'reset', generation: ++generation.current });
  }, []);
  useEffect(
    () => () => {
      request.current?.abort();
      generation.current++;
    },
    [],
  );
  const {
    data,
    status,
    error: connectionError,
    lastUpdated,
    refresh,
  } = useMatchData(matchId, {
    onReset: reset,
    includeGraph: false,
    enabled: !sharedPlayback || sharedPlayback.ready,
    pollInterval: sharedPlayback ? 750 : 2000,
  });
  const briefing = summary?.fan_briefing;
  const teams = teamsForScenario(scenarioId);
  const events =
    reviewing && briefing?.snapshot
      ? data.events.filter((event) => event.sequence <= briefing.snapshot.through_sequence)
      : data.events;
  const important = featuredMoment(events);
  const second = events.at(-1)?.match_second ?? 0;
  const finished = events.at(-1)?.type === 'match_end';
  const inspectorUrl = `/?view=development&match=${encodeURIComponent(matchId)}&scenario=${encodeURIComponent(scenarioId)}${sharedPlayback?.dayId ? `&day=${encodeURIComponent(sharedPlayback.dayId)}` : ''}`;

  async function pause() {
    setRunning(false);
    setReviewing(true);
    await (sharedPlayback ? sharedPlayback.pause() : playback.current?.pause());
  }
  async function catchUp(style = audience, sinceOverride) {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const current = generation.current;
    dispatch({ type: 'start', generation: current });
    try {
      await pause();
      if (controller.signal.aborted) return;
      const next = await postCatchUp(
        matchId,
        {
          since_sequence: sinceOverride ?? cursor.current,
          audience: style,
        },
        { signal: controller.signal },
      );
      if (!controller.signal.aborted && current === generation.current) {
        cursor.current = next.through_sequence;
        dispatch({ type: 'success', generation: current, result: retainCatchUp(summary, next) });
        await refresh(controller.signal);
      }
    } catch (err) {
      if (!controller.signal.aborted && current === generation.current)
        dispatch({
          type: 'failure',
          generation: current,
          error: err.message || 'The recap could not load. Try again.',
        });
    } finally {
      if (request.current === controller) request.current = null;
    }
  }
  function clearReview() {
    request.current?.abort();
    request.current = null;
    dispatch({ type: 'reset', generation: ++generation.current });
    setReviewing(false);
    setPitchRequest({ latest: true, nonce: Date.now() });
  }
  useEffect(() => {
    if (sharedPlayback?.running) clearReview();
  }, [sharedPlayback?.running]);
  function changeRunning(next) {
    if (next) clearReview();
    setRunning(next);
  }
  function continueMatch() {
    if (sharedPlayback) {
      clearReview();
      if (!finished) sharedPlayback.resume();
    } else if (finished) clearReview();
    else playback.current?.resume();
  }
  async function replay(event) {
    if (!event) return;
    await pause();
    setPitchRequest({ id: event.event_id, nonce: Date.now() });
  }

  return (
    <div className="matchos-app fan-main" style={variablesForTeams(teams)}>
      <MatchHeader compact status={status} error={connectionError} lastUpdated={lastUpdated} />
      <main className="fan-match-flow">
        <Scoreboard compact analytics={data.analytics} events={events} fixtureTeams={teams} />
        {sharedPlayback ? (
          sharedPlayback.controls
        ) : (
          <ReplayControls
            compact
            controlsRef={playback}
            running={running}
            onRunningChange={changeRunning}
            matchId={matchId}
            scenarioId={scenarioId}
            hasEvents={data.events.length > 0}
            observedSequence={data.events.at(-1)?.sequence ?? 0}
            loading={status === 'loading'}
            autoStart={autoStart}
            onNewMatch={onNewMatch}
            onScenarioChange={onScenarioChange}
          />
        )}
        {reviewing && (
          <div className="fan-review-state" role="status">
            <span>
              {es
                ? `Revisando la acción hasta ${formatMatchSecond(second)}.`
                : `Reviewing action up to ${formatMatchSecond(second)}.`}
              <small>
                {es
                  ? sharedPlayback
                    ? 'Los tres partidos están en pausa mientras repasas lo ocurrido.'
                    : 'El partido está en pausa mientras repasas lo ocurrido.'
                  : sharedPlayback
                    ? 'All three matches are paused while you look back.'
                    : 'The match is paused while you look back.'}
              </small>
            </span>
            <button className="btn-primary" onClick={continueMatch}>
              {es
                ? finished
                  ? 'Ver el final'
                  : 'Continuar partido'
                : finished
                  ? 'Back to final action'
                  : 'Continue match'}
            </button>
          </div>
        )}
        <section className="fan-important-moment" aria-label="Important match moment">
          <div>
            <span className="feature-pill">{es ? 'En el campo' : 'On the pitch'}</span>
            <h2>
              {important
                ? `${important.player_name || important.team_name} · ${formatMatchSecond(important.match_second)}`
                : es
                  ? 'La historia empieza aquí.'
                  : 'The story starts here.'}
            </h2>
          </div>
          {important && (
            <button className="btn-primary" onClick={() => replay(important)}>
              {important.type === 'goal'
                ? es
                  ? 'Ver el gol'
                  : 'See the goal'
                : important.type === 'red_card'
                  ? es
                    ? 'Ver la tarjeta roja'
                    : 'See the red card'
                  : es
                    ? 'Ver la ocasión'
                    : 'See the chance'}
            </button>
          )}
        </section>
        <PitchReplay
          compact
          events={events}
          request={pitchRequest}
          language={language}
          home={teams.home.name}
          away={teams.away.name}
          showContinue={false}
          onMomentSelect={() => pause()}
          onLatest={continueMatch}
        />
        <FocusedRecap
          briefing={briefing}
          summary={summary}
          events={events}
          busy={busy}
          error={error}
          audience={audience}
          language={language}
          onLanguageChange={setLanguage}
          onListen={pause}
          onAudienceChange={(style) => {
            setAudience(style);
            if (briefing) catchUp(style, briefing.snapshot.since_sequence);
          }}
          onCatchUp={() => catchUp()}
          onReplayMoment={replay}
        />
      </main>
      <footer className="dashboard-footer">
        <p>MatchOS · Real club and player names. Fictional match action.</p>
        <p>Independent hackathon prototype · No endorsement claimed.</p>
        <a href={inspectorUrl}>Development dashboard</a>
      </footer>
    </div>
  );
}

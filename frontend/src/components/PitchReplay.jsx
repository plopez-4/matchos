import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import {
  pitchMoves,
  actionCaption,
  actionTrail,
  actionParticipants,
  actionDuration,
  replayTransition,
} from '../utils/pitchReplay';
import { formatMatchSecond } from '../utils/formatters';
import { clubByName } from '../utils/teams';

export function PitchReplay({
  events = [],
  request = null,
  home = 'Home',
  away = 'Away',
  compact = false,
  language = 'en',
  showContinue = true,
  onMomentSelect,
  onLatest,
}) {
  const es = language === 'es';
  const moves = useMemo(() => pitchMoves(events), [events]);
  const newestMove = useRef(null);
  newestMove.current = moves.at(-1);
  const [moveId, setMoveId] = useState(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [latest, setLatest] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [pending, setPending] = useState(null);
  const [transitionLabel, setTransitionLabel] = useState('');
  const [playbackId, setPlaybackId] = useState(0);
  const panel = useRef(null);
  const marker = `replay-${useId().replaceAll(':', '')}`;
  const move = moves.find((m) => m.id === moveId) ?? moves.at(-1);
  const safeStep = Math.min(step, (move?.events.length ?? 1) - 1);
  const event = move?.events[safeStep];
  const end = safeStep >= (move?.events.length ?? 0) - 1;
  const duration = event ? actionDuration(event, move?.events[safeStep + 1], speed) : 1400;
  const requestMoveId = request
    ? moves.find((m) => m.events.some((e) => e.event_id === request.id))?.id
    : null;

  useEffect(() => {
    if (!moves.some((m) => m.id === moveId)) {
      setMoveId(moves.at(-1)?.id ?? null);
      setStep(0);
      setPending(null);
    }
  }, [moves, moveId]);

  function goTo(target, position = 0, label = null) {
    if (!target) return;
    const cut = label ?? replayTransition(event, target.events[position]);
    if (event && cut) {
      setPending({ moveId: target.id, step: position, label: cut });
      setTransitionLabel(cut);
    } else {
      setMoveId(target.id);
      setStep(position);
      setPlaybackId((value) => value + 1);
    }
  }

  useEffect(() => {
    if (!pending || !playing) return;
    const timer = setTimeout(() => {
      setMoveId(pending.moveId);
      setStep(pending.step);
      setPending(null);
      setPlaybackId((value) => value + 1);
    }, 1200 / speed);
    return () => clearTimeout(timer);
  }, [pending, playing, speed]);

  useEffect(() => {
    if (!request) return;
    if (request.latest) {
      goTo(newestMove.current, 0, 'Returning to the latest recorded move');
      setLatest(true);
      setPlaying(true);
      if (!compact) {
        panel.current?.scrollIntoView({ block: 'center', behavior: 'instant' });
        panel.current?.focus({ preventScroll: true });
      }
      return;
    }
    const target = moves.find((m) => m.events.some((e) => e.event_id === request.id));
    if (!target) return;
    goTo(target, 0, `Build-up begins · ${formatMatchSecond(target.events[0].match_second)}`);
    setPlaying(true);
    setLatest(false);
    if (!compact) {
      panel.current?.scrollIntoView({ block: 'center', behavior: 'instant' });
      panel.current?.focus({ preventScroll: true });
    }
  }, [request, requestMoveId]);

  useEffect(() => {
    if (!playing || !move || pending) return;
    const timer = setInterval(() => {
      if (!end) {
        goTo(move, safeStep + 1);
      } else if (latest && newestMove.current?.id !== move.id) {
        goTo(newestMove.current);
      } else if (!latest) setPlaying(false);
    }, duration);
    return () => clearInterval(timer);
  }, [playing, move?.id, safeStep, move?.events.length, latest, speed, pending, duration]);

  function replay(target) {
    goTo(target, 0, `Build-up begins · ${formatMatchSecond(target.events[0].match_second)}`);
    setLatest(false);
    setPlaying(true);
    onMomentSelect?.(
      target.events.find((e) => e.type === 'goal') ??
        target.events.find((e) => e.type === 'red_card') ??
        target.events.find((e) => e.type === 'shot') ??
        target.events.at(-1),
    );
  }
  const x = (n) => 60 + n * 10.8;
  const y = (n) => 50 + n * 6.8;
  const pathEvents = move ? actionTrail(move.events, safeStep) : [];
  const participants = actionParticipants(event, move?.events[safeStep - 1]);
  const isVector = event && ['pass', 'shot'].includes(event.type);
  const color =
    clubByName(event?.team_name)?.color ?? (event?.team_id === 'away' ? '#ff668c' : '#7dd3fc');
  const ballX = event ? x(isVector ? event.end_x : event.x) : 600;
  const ballY = event ? y(isVector ? event.end_y : event.y) : 390;
  const moments = moves
    .filter((m) => m.events.some((e) => ['shot', 'goal', 'red_card'].includes(e.type)))
    .slice(-6)
    .reverse();
  return (
    <section
      className={`dashboard-card pitch-replay ${compact ? 'pitch-replay-compact' : ''}`}
      aria-label="Match pitch replay"
      tabIndex={-1}
      ref={panel}
    >
      {!compact && (
        <div className="card-header">
          <div>
            <span className="feature-pill">On the pitch</span>
            <h2>{latest ? 'Follow the move.' : 'How it unfolded.'}</h2>
          </div>
          <span className="pitch-time">
            {event ? formatMatchSecond(event.match_second) : '0:00'} ·{' '}
            {latest ? 'Latest recorded move' : 'Moment replay'}
          </span>
        </div>
      )}
      {!compact && (
        <div className="pitch-score-strip">
          <span>{home} →</span>
          <span>← {away}</span>
        </div>
      )}
      {compact && (
        <div className="focus-pitch-meta">
          <span>
            {latest
              ? es
                ? 'Última jugada registrada'
                : 'Latest recorded move'
              : es
                ? 'Repetición de la jugada'
                : 'Build-up replay'}
          </span>
          <span>{event ? formatMatchSecond(event.match_second) : '0:00'}</span>
        </div>
      )}
      <p className="pitch-transition" role="status">
        {es
          ? 'Posiciones registradas del balón · repetición resumida'
          : transitionLabel || 'Recorded action locations · compressed replay'}
      </p>
      <svg
        className="match-pitch"
        viewBox="0 0 1200 780"
        role="img"
        aria-labelledby={`${marker}-title`}
      >
        <title id={`${marker}-title`}>
          {`${actionCaption(event)} Schematic replay between recorded ball locations, not continuous player tracking.`}
        </title>
        <defs>
          <pattern id={`${marker}-grass`} width="180" height="780" patternUnits="userSpaceOnUse">
            <rect width="180" height="780" fill="#124e3c" />
            <rect width="90" height="780" fill="#155b43" />
          </pattern>
          <marker
            id={`${marker}-arrow`}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="4"
            markerHeight="4"
            orient="auto"
          >
            <path d="M0 0L10 5L0 10Z" fill="#e4ffdb" />
          </marker>
        </defs>
        <rect width="1200" height="780" rx="22" fill={`url(#${marker}-grass)`} />
        <g stroke="#ffffff88" strokeWidth="3" fill="none">
          <rect x="60" y="50" width="1080" height="680" />
          <path d="M600 50V730M60 190H225V590H60M1140 190H975V590H1140M60 295H115V485H60M1140 295H1085V485H1140M60 350H30V430H60M1140 350H1170V430H1140" />
          <circle cx="600" cy="390" r="91" />
          <circle cx="600" cy="390" r="4" fill="white" />
          <circle cx="170" cy="390" r="4" fill="white" />
          <circle cx="1030" cy="390" r="4" fill="white" />
          <path d="M225 315Q280 390 225 465M975 315Q920 390 975 465" />
        </g>
        <g className={`pitch-action-layer${pending ? ' is-cut' : ''}`}>
          {pathEvents.map((e) => (
            <g key={e.event_id} opacity={e.event_id === event?.event_id ? 1 : 0.25}>
              <line
                x1={x(e.x)}
                y1={y(e.y)}
                x2={x(e.end_x)}
                y2={y(e.end_y)}
                stroke={e.type === 'shot' ? '#ffe171' : '#e4ffdb'}
                strokeWidth={e.type === 'shot' ? 6 : 4}
                strokeDasharray={e.type === 'pass' ? '12 10' : undefined}
                markerEnd={`url(#${marker}-arrow)`}
              />
              <circle className="pitch-trail-point" cx={x(e.x)} cy={y(e.y)} r="5" fill="#d1e5d9" />
            </g>
          ))}
          {participants.map((person) => (
            <g
              key={person.id}
              className="pitch-participant"
              aria-label={`${person.role}: ${person.name}${person.number ? `, number ${person.number}` : ''}`}
            >
              <title>{`${person.role}: ${person.name}`}</title>
              <circle
                cx={x(person.x)}
                cy={y(person.y)}
                r="23"
                fill={color}
                fillOpacity="0.5"
                stroke="white"
                strokeWidth="3"
              />
              <rect
                x={x(person.x) - 21}
                y={Math.max(8, y(person.y) - 59)}
                width="42"
                height="29"
                rx="8"
                fill="#082b22"
                stroke="#ffffff80"
              />
              <text
                x={x(person.x)}
                y={Math.max(8, y(person.y) - 59) + 21}
                textAnchor="middle"
                fill="white"
                fontSize="22"
                fontWeight="800"
              >
                {person.number ||
                  person.name
                    .split(/\s+/)
                    .slice(0, 2)
                    .map((part) => part[0])
                    .join('')
                    .toUpperCase()}
              </text>
            </g>
          ))}
          {event && (
            <g
              key={`${event.event_id}-${playbackId}`}
              className={isVector ? 'pitch-moving-event' : ''}
            >
              <circle
                className="pitch-ball-static"
                cx={ballX}
                cy={ballY}
                r="11"
                fill="white"
                stroke="#122e27"
                strokeWidth="4"
              />
              {isVector && (
                <circle
                  className="pitch-ball-moving"
                  r="11"
                  fill="white"
                  stroke="#122e27"
                  strokeWidth="4"
                  style={{
                    '--pitch-start-x': `${x(event.x)}px`,
                    '--pitch-start-y': `${y(event.y)}px`,
                    '--pitch-end-x': `${ballX}px`,
                    '--pitch-end-y': `${ballY}px`,
                    animationDuration: `${Math.max(300, duration - 250 / speed)}ms`,
                    animationPlayState: playing && !pending ? 'running' : 'paused',
                  }}
                />
              )}
              <rect x="325" y="660" width="550" height="44" rx="22" fill="#082b22e6" />
              <text x="600" y="689" textAnchor="middle" fill="white" fontSize="22" fontWeight="700">
                {event.player_name || event.player_id}{' '}
                {event.recipient_player_id
                  ? `→ ${event.recipient_player_name || event.recipient_player_id}`
                  : ''}
              </text>
            </g>
          )}
        </g>
        {pending && (
          <g className="pitch-cut-overlay" aria-hidden="true">
            <rect x="100" y="300" width="1000" height="160" rx="22" fill="#082b22f2" />
            <text x="600" y="370" textAnchor="middle" fill="white" fontSize="29" fontWeight="700">
              {es ? 'Nueva jugada registrada' : 'A new recorded moment'}
            </text>
            <text x="600" y="415" textAnchor="middle" fill="#b9d7c6" fontSize="23">
              {pending.label}
            </text>
          </g>
        )}
        {!event && (
          <text x="600" y="390" textAnchor="middle" fill="white" fontSize="28">
            {es
              ? 'Inicia el partido para ver el balón en movimiento.'
              : 'Start the match to see the ball move.'}
          </text>
        )}
      </svg>
      {participants.length > 0 && (
        <div className="pitch-participant-key" aria-label="Players in this recorded action">
          {participants.map((person) => (
            <span key={person.id}>
              <b>{person.role}</b> {person.number ? `#${person.number} ` : ''}
              {person.name}
            </span>
          ))}
        </div>
      )}
      <p className="pitch-replay-note">
        White ball · small dots show earlier ball locations · only recorded participants shown
      </p>
      <p
        className={`pitch-commentary ${event?.type === 'goal' || event?.outcome === 'goal' ? 'is-goal' : ''}`}
      >
        {actionCaption(event)}
      </p>
      <div className="pitch-controls">
        <button
          className={compact ? 'focus-text-button' : 'btn-primary'}
          disabled={!event}
          onClick={() => {
            if (!playing && end && !latest)
              goTo(move, 0, `Build-up begins · ${formatMatchSecond(move.events[0].match_second)}`);
            setPlaying(!playing);
          }}
        >
          {compact
            ? playing
              ? es
                ? 'Pausar repetición'
                : 'Pause replay'
              : es
                ? 'Reproducir repetición'
                : 'Play replay'
            : playing
              ? 'Pause pitch'
              : es
                ? 'Reproducir jugada'
                : 'Play move'}
        </button>
        {!compact && (
          <button className="replay-reset" disabled={!move} onClick={() => replay(move)}>
            Replay this move
          </button>
        )}
        {!latest && showContinue && (
          <button
            className="replay-reset"
            onClick={() => {
              goTo(moves.at(-1), 0, 'Returning to the latest recorded move');
              setLatest(true);
              setPlaying(true);
              onLatest?.();
            }}
          >
            {es ? 'Continuar partido →' : compact ? 'Continue match →' : 'Back to latest'}
          </button>
        )}
        {!compact && (
          <label>
            Move speed{' '}
            <select
              aria-label="Pitch replay speed"
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
            >
              <option value={0.5}>Slow</option>
              <option value={1}>Normal</option>
              <option value={2}>Fast</option>
            </select>
          </label>
        )}
      </div>
      {moments.length > 0 && (
        <details className="focus-moments-disclosure" open={compact ? undefined : true}>
          {compact && <summary>{es ? 'Momentos anteriores' : 'Earlier moments'}</summary>}
          <div className="pitch-moments" aria-label="Replay key moments">
            {moments.map((m) => {
              const key =
                m.events.find((e) => e.type === 'goal') ??
                m.events.find((e) => e.type === 'red_card') ??
                m.events.find((e) => e.type === 'shot');
              const isCard = key.type === 'red_card';
              return (
                <button
                  key={m.id}
                  className={isCard ? 'moment-red-card' : ''}
                  aria-pressed={!latest && m.id === move?.id}
                  onClick={() => replay(m)}
                >
                  <span>
                    {key.type === 'goal'
                      ? es
                        ? '⚽ Gol'
                        : '⚽ Goal'
                      : isCard
                        ? es
                          ? '🟥 Tarjeta roja'
                          : '🟥 Red card'
                        : es
                          ? '↗ Ocasión'
                          : '↗ Chance'}{' '}
                    · {formatMatchSecond(key.match_second)}
                  </span>
                  <small>{key.team_name || key.team_id}</small>
                </button>
              );
            })}
          </div>
        </details>
      )}
      {!compact && (
        <p className="card-subtitle">
          Synthetic event replay. Lines connect recorded endpoints; travel between them is
          illustrative. Cuts mark missing action. Choose a moment to hold its build-up through the
          shot.
        </p>
      )}
    </section>
  );
}

import { formatMatchSecond } from './formatters.js';

const point = (x, y) => [x, y].every((n) => Number.isFinite(n) && n >= 0 && n <= 100);
const vector = (event) => ['pass', 'shot'].includes(event?.type);
const samePoint = (a, b) =>
  point(a[0], a[1]) &&
  point(b[0], b[1]) &&
  Math.abs(a[0] - b[0]) < 0.001 &&
  Math.abs(a[1] - b[1]) < 0.001;

// Continuity is conservative: unknown movement/identity is a cut, never a guessed carry.
export function connectedActions(previous, next) {
  if (
    !previous ||
    !next ||
    !previous.possession_id ||
    ['match_id', 'team_id', 'period', 'possession_id'].some((key) => previous[key] !== next[key]) ||
    next.sequence !== previous.sequence + 1 ||
    next.match_second < previous.match_second ||
    next.match_second - previous.match_second > 10 ||
    ['recovery', 'kickoff'].includes(next.type)
  )
    return false;
  const endpoint = vector(previous) ? [previous.end_x, previous.end_y] : [previous.x, previous.y];
  if (!samePoint(endpoint, [next.x, next.y])) return false;
  if (previous.type === 'pass')
    return previous.outcome === 'complete' && previous.recipient_player_id === next.player_id;
  if (previous.type === 'shot')
    return (
      previous.outcome === 'goal' &&
      next.type === 'goal' &&
      next.related_event_id === previous.event_id &&
      next.player_id === previous.player_id
    );
  return ['recovery', 'kickoff'].includes(previous.type) && previous.player_id === next.player_id;
}

export function replayTransition(previous, next) {
  if (!previous || !next || connectedActions(previous, next)) return null;
  const seconds = next.match_second - previous.match_second;
  const kind =
    seconds < 0
      ? 'Earlier build-up'
      : previous.possession_id !== next.possession_id ||
          previous.team_id !== next.team_id ||
          previous.period !== next.period
        ? 'Next recorded possession'
        : 'Gap in recorded action';
  return `${kind} · ${formatMatchSecond(next.match_second)}${seconds > 0 ? ` · ${seconds} seconds later` : ''}`;
}

export function actionTrail(events, step) {
  let first = step;
  while (first > 0 && connectedActions(events[first - 1], events[first])) first--;
  return events.slice(first, step + 1).filter(vector);
}

// Compressed viewing time, not inferred ball speed or measured flight duration.
export function actionDuration(event, next, speed = 1) {
  const seconds = next ? next.match_second - event.match_second : 5;
  return Math.min(2400, Math.max(1400, seconds * 350)) / speed;
}

export function actionParticipants(event, previous) {
  if (!event) return [];
  // A goal location is the ball crossing the line, not a runner at the goal line.
  const origin =
    event.type === 'goal'
      ? previous?.type === 'shot' && connectedActions(previous, event)
        ? previous
        : null
      : event;
  if (!origin) return [];
  const people = [
    {
      id: event.player_id,
      name: event.player_name || event.player_id,
      number: event.player_shirt_number,
      x: origin.x,
      y: origin.y,
      role: ['shot', 'goal'].includes(event.type)
        ? 'Shooter'
        : event.type === 'pass'
          ? 'Passer'
          : 'On the ball',
    },
  ];
  if (event.type === 'pass' && event.outcome === 'complete' && event.recipient_player_id) {
    people.push({
      id: event.recipient_player_id,
      name: event.recipient_player_name || event.recipient_player_id,
      number: event.recipient_player_shirt_number,
      x: event.end_x,
      y: event.end_y,
      role: 'Receiver',
    });
  }
  return people.filter((person) => point(person.x, person.y));
}

// Group only contiguous, observed actions. Never bridge teams or possessions.
export function pitchMoves(events = []) {
  const groups = [];
  const ordered = [...events].sort((a, b) => a.sequence - b.sequence);
  let group;
  for (const event of ordered) {
    if (!['kickoff', 'recovery', 'pass', 'shot', 'goal'].includes(event.type)) {
      group = null;
      continue;
    }
    if (
      !point(event.x, event.y) ||
      (['pass', 'shot'].includes(event.type) && !point(event.end_x, event.end_y))
    ) {
      group = null;
      continue;
    }
    if (
      !group ||
      group.match_id !== event.match_id ||
      group.team_id !== event.team_id ||
      group.period !== event.period ||
      group.possession_id !== event.possession_id ||
      ['kickoff', 'recovery'].includes(event.type)
    ) {
      group = {
        id: event.event_id,
        match_id: event.match_id,
        team_id: event.team_id,
        period: event.period,
        possession_id: event.possession_id,
        events: [],
      };
      groups.push(group);
    }
    group.events.push(event);
  }
  return groups;
}

export function actionCaption(event) {
  if (!event) return 'Waiting for the first recorded move.';
  const player = event.player_name || event.player_id || 'Player';
  const recipient = event.recipient_player_name || event.recipient_player_id;
  if (event.type === 'pass')
    return `${player} ${event.outcome === 'complete' ? 'finds' : 'passes toward'} ${recipient || 'a teammate'}.`;
  if (event.type === 'goal') return `${player} scores for ${event.team_name || event.team_id}.`;
  if (event.type === 'shot')
    return `${player} shoots${event.outcome === 'goal' ? ' — goal!' : event.outcome ? ` — ${event.outcome}.` : '.'}`;
  if (event.type === 'recovery')
    return `${player} wins the ball for ${event.team_name || event.team_id}.`;
  return `${event.team_name || event.team_id} restart from the centre.`;
}

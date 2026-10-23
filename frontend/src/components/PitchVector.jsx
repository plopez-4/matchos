import React, { useId } from 'react';

export function vectorEvent(event, events = []) {
  if (!['pass', 'shot', 'goal'].includes(event.type)) return null;
  const complete = (item) =>
    item &&
    [item.x, item.y, item.end_x, item.end_y].every((n) => Number.isFinite(n) && n >= 0 && n <= 100);
  if (complete(event)) return event;
  if (event.type !== 'goal' || !event.related_event_id) return null;
  const shot = events.find(
    (item) =>
      item.event_id === event.related_event_id &&
      item.type === 'shot' &&
      item.team_id === event.team_id &&
      item.player_id === event.player_id &&
      item.match_id === event.match_id &&
      item.sequence < event.sequence &&
      item.match_second <= event.match_second &&
      item.outcome === 'goal',
  );
  return complete(shot) ? shot : null;
}

export function PitchVector({ event, events = [], language = 'en' }) {
  const id = `pitch-${useId().replaceAll(':', '')}`;
  const vector = vectorEvent(event, events);
  if (!vector) return null;
  const spanish = language === 'es';
  const x = (n) => 6 + n * 1.08,
    y = (n) => 6 + n * 0.68;
  const moved = vector.x !== vector.end_x || vector.y !== vector.end_y;
  const linked = vector.event_id !== event.event_id;
  const color =
    vector.type === 'pass' ? '#38bdf8' : vector.outcome === 'goal' ? '#00ff85' : '#ff5777';
  const label = `${event.player_name || event.player_id}: (${vector.x}, ${vector.y}) → (${vector.end_x}, ${vector.end_y})`;
  return (
    <figure className="pitch-vector">
      <svg width="120" height="80" viewBox="0 0 120 80" role="img" aria-labelledby={`${id}-title`}>
        <title id={`${id}-title`}>{label}</title>
        <defs>
          <marker
            id={`${id}-arrow`}
            viewBox="0 0 6 6"
            refX="5"
            refY="3"
            markerWidth="4"
            markerHeight="4"
            orient="auto"
          >
            <path d="M0 0L6 3L0 6Z" fill={color} />
          </marker>
        </defs>
        <g fill="none" stroke="#ffffff55" strokeWidth="0.8">
          <rect x="6" y="6" width="108" height="68" rx="1" />
          <path d="M60 6V74M6 23H23V57H6M114 23H97V57H114M6 31H13V49H6M114 31H107V49H114M6 36H3V44H6M114 36H117V44H114" />
          <circle cx="60" cy="40" r="9" />
        </g>
        {moved && (
          <line
            className="pitch-vector-line"
            x1={x(vector.x)}
            y1={y(vector.y)}
            x2={x(vector.end_x)}
            y2={y(vector.end_y)}
            stroke={color}
            strokeWidth="2"
            strokeDasharray="4 3"
            markerEnd={`url(#${id}-arrow)`}
          />
        )}
        <circle cx={x(vector.x)} cy={y(vector.y)} r="2" fill={color} />
      </svg>
      <figcaption>
        {linked
          ? spanish
            ? 'Remate registrado vinculado al gol'
            : 'Recorded shot linked to goal'
          : spanish
            ? 'Vector registrado'
            : 'Recorded vector'}{' '}
        · {event.player_name || event.player_id}
      </figcaption>
    </figure>
  );
}

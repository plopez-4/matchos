import React from 'react';
import { formatMatchSecond, formatTeamName, formatEventType, formatOutcome } from '../utils/formatters';

export function EvidenceList({ evidenceIds = [], events = [], onSelectEvent }) {
  if (!evidenceIds || evidenceIds.length === 0) {
    return <p className="evidence-empty">No supporting events recorded.</p>;
  }

  return (
    <ul className="evidence-list" aria-label="Supporting events list">
      {evidenceIds.map(id => {
        const event = events.find(e => e.event_id === id);

        if (!event) {
          return (
            <li key={id} className="evidence-item evidence-item-missing">
              <span className="evidence-badge badge-missing">Missing from feed</span>
              <span className="evidence-text">Event data not yet loaded in current snapshot</span>
              <code className="evidence-id">{id}</code>
            </li>
          );
        }

        const time = formatMatchSecond(event.match_second);
        const team = formatTeamName(event.team_id);
        const type = formatEventType(event.type);
        const outcome = formatOutcome(event.outcome);

        return (
          <li key={id} className="evidence-item">
            <div className="evidence-main">
              <span className="evidence-time">{time}</span>
              <span className={`evidence-team team-${event.team_id}`}>{team}</span>
              <span className={`evidence-type type-${event.type}`}>{type}</span>
              {outcome && <span className={`evidence-outcome outcome-${event.outcome}`}>{outcome}</span>}
              {typeof event.x === 'number' && (
                <span className="evidence-coords" title={`Pitch coordinate x: ${event.x}`}>
                  pitch: {Math.round(event.x)}m
                </span>
              )}
            </div>

            <div className="evidence-actions">
              <code className="evidence-id">{id}</code>
              {onSelectEvent && (
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => onSelectEvent(id)}
                  title="Highlight this event in the match timeline"
                >
                  Find in timeline
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

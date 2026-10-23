import React, { useState } from 'react';
import { PitchVector, vectorEvent } from './PitchVector';
import {
  formatMatchSecond,
  formatTeamName,
  formatEventType,
  formatOutcome,
} from '../utils/formatters';

function InspectPitch({ event, events, language }) {
  const [open, setOpen] = useState(false);
  if (!vectorEvent(event, events)) return null;
  return (
    <details className="pitch-inspection" onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>{language === 'es' ? 'Ver vector registrado' : 'View recorded vector'}</summary>
      {open && <PitchVector event={event} events={events} language={language} />}
    </details>
  );
}

export function EvidenceList({ evidenceIds = [], events = [], onSelectEvent, language = 'en' }) {
  const spanish = language === 'es';
  const eventLabels = {
    goal: 'Gol',
    shot: 'Remate',
    pass: 'Pase',
    recovery: 'Recuperación',
    kickoff: 'Saque inicial',
    substitution: 'Sustitución',
    half_end: 'Fin de la primera parte',
    match_end: 'Final',
  };
  const outcomeLabels = {
    complete: 'Completado',
    intercepted: 'Interceptado',
    saved: 'Parado',
    blocked: 'Bloqueado',
    missed: 'Fuera',
    goal: 'Gol',
  };
  if (!evidenceIds || evidenceIds.length === 0) {
    return (
      <p className="evidence-empty">
        {spanish ? 'No se registraron eventos de respaldo.' : 'No supporting events recorded.'}
      </p>
    );
  }

  return (
    <ul
      className="evidence-list"
      aria-label={spanish ? 'Lista de eventos de respaldo' : 'Supporting events list'}
    >
      {evidenceIds.map((id) => {
        const event = events.find((e) => e.event_id === id);

        if (!event) {
          return (
            <li key={id} className="evidence-item evidence-item-missing">
              <span className="evidence-badge badge-missing">
                {spanish ? 'Evento no disponible' : 'Missing from feed'}
              </span>
              <span className="evidence-text">
                {spanish
                  ? 'El evento aún no está cargado en esta vista'
                  : 'Event data not yet loaded in current snapshot'}
              </span>
              <code className="evidence-id">{id}</code>
            </li>
          );
        }

        const time = formatMatchSecond(event.match_second);
        const team = event.team_name || formatTeamName(event.team_id);
        const type = spanish ? eventLabels[event.type] || event.type : formatEventType(event.type);
        const outcome = spanish
          ? outcomeLabels[event.outcome] || event.outcome
          : formatOutcome(event.outcome);

        return (
          <li key={id} className="evidence-item">
            <div className="evidence-main">
              <span className="evidence-time">{time}</span>
              <span className={`evidence-team team-${event.team_id}`}>{team}</span>
              <span className={`evidence-type type-${event.type}`}>{type}</span>
              <span className="evidence-player">
                {event.player_name || event.player_id}
                {event.player_shirt_number != null && <> · #{event.player_shirt_number}</>}
              </span>
              {event.recipient_player_id && (
                <span className="evidence-player">
                  → {event.recipient_player_name || event.recipient_player_id}
                  {event.recipient_player_shirt_number != null && (
                    <> · #{event.recipient_player_shirt_number}</>
                  )}
                </span>
              )}
              {event.player_position && (
                <span className="evidence-coords">
                  {spanish ? 'Rol de demostración' : 'Demo role'}: {event.player_position}
                </span>
              )}
              {event.roster_version && (
                <span className="evidence-coords">
                  {spanish
                    ? 'Acción sintética · identidad de referencia'
                    : 'Synthetic action · reference identity'}
                </span>
              )}
              {outcome && (
                <span className={`evidence-outcome outcome-${event.outcome}`}>{outcome}</span>
              )}
              {typeof event.x === 'number' && (
                <span className="evidence-coords" title={`Pitch coordinate x: ${event.x}`}>
                  {spanish ? 'campo' : 'pitch'} x: {Math.round(event.x)}/100
                </span>
              )}
              {typeof event.y === 'number' && (
                <span className="evidence-coords">y: {Math.round(event.y)}/100</span>
              )}
              {typeof event.end_x === 'number' && typeof event.end_y === 'number' && (
                <span className="evidence-coords">
                  → ({Math.round(event.end_x)}, {Math.round(event.end_y)})/100
                </span>
              )}
            </div>

            <InspectPitch event={event} events={events} language={language} />
            <div className="evidence-actions">
              <code className="evidence-id">{id}</code>
              {onSelectEvent && (
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => onSelectEvent(id)}
                  title={
                    spanish
                      ? 'Resaltar este evento en la cronología del partido'
                      : 'Highlight this event in the match timeline'
                  }
                >
                  {spanish ? 'Ver en la cronología' : 'Find in timeline'}
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

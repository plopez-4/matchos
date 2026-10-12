import React from 'react';
import { EvidenceList } from './EvidenceList';

export function MatchStoryBriefing({ briefing, events = [], onSelectEvent }) {
  if (!briefing) return null;
  return (
    <article className="catchup-section-card match-story-briefing" aria-label="Match story">
      <h3 className="section-card-title">{briefing.headline}</h3>
      <p className="section-card-text">
        {briefing.scoreline} · {briefing.clock}
      </p>
      <ul className="match-story-points">
        {briefing.sections.map((section) => (
          <li key={section.title}>
            <strong>{section.title}</strong>
            <p className="section-card-text">{section.text}</p>
          </li>
        ))}
      </ul>
      <details>
        <summary>See the supporting events and score path</summary>
        <p className="card-subtitle">
          Evidence-backed synthetic action. Recent shot windows use an exclusive start.
        </p>
        {briefing.window && (
          <p className="card-subtitle">
            Window: ({briefing.window.start_exclusive}, {briefing.window.end_inclusive}] match
            seconds.
          </p>
        )}
        {briefing.trajectory?.transitions?.length > 0 && (
          <ol>
            {briefing.trajectory.transitions.map((step) => (
              <li key={step.sequence}>
                {Math.floor(step.match_second / 60)}:
                {String(step.match_second % 60).padStart(2, '0')} · {step.after.home}–
                {step.after.away} · {step.type.replaceAll('_', ' ')}
              </li>
            ))}
          </ol>
        )}
        <EvidenceList
          evidenceIds={briefing.evidence_event_ids}
          events={events}
          onSelectEvent={onSelectEvent}
        />
      </details>
    </article>
  );
}

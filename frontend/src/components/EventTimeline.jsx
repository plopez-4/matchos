import React, { useState, useMemo, useEffect, useRef } from 'react';
import { visibleTimelineEvents } from '../utils/timeline';
import { formatMatchSecond, formatTeamName, formatEventType, formatOutcome } from '../utils/formatters';

export function EventTimeline({ events = [], highlightedEventId = null, onClearHighlight }) {
  const [filter, setFilter] = useState('all'); // 'all' | 'key' | 'pass' | 'recovery'
  const [showAll, setShowAll] = useState(false);
  const highlightedElement = useRef(null);
  const targetPresent = events.some(e => e.event_id === highlightedEventId);
  useEffect(() => {
    if (!highlightedEventId) return;
    highlightedElement.current?.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
      block: 'center',
    });
  }, [highlightedEventId, targetPresent]);

  // Sort newest first by sequence (so equal timestamps preserve sequence order)
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => b.sequence - a.sequence);
  }, [events]);

  const filteredEvents = useMemo(() => {
    switch (filter) {
      case 'key':
        return sortedEvents.filter(e => e.type === 'goal' || e.type === 'shot');
      case 'pass':
        return sortedEvents.filter(e => e.type === 'pass');
      case 'recovery':
        return sortedEvents.filter(e => e.type === 'recovery');
      case 'all':
      default:
        return sortedEvents;
    }
  }, [sortedEvents, filter]);

  const displayEvents = visibleTimelineEvents(events, filter, showAll, highlightedEventId);

  const getEventBadgeClass = (type) => {
    switch (type) {
      case 'goal': return 'badge-goal';
      case 'shot': return 'badge-shot';
      case 'recovery': return 'badge-recovery';
      case 'pass': return 'badge-pass';
      case 'kickoff': return 'badge-kickoff';
      default: return 'badge-default';
    }
  };

  return (
    <section className="dashboard-card timeline-card" aria-label="Recent Match Events Timeline">
      <div className="card-header">
        <div className="header-text-group">
          <div className="title-with-pill">
            <h2 className="card-title">Match Highlights Timeline</h2>
            <span className="feature-pill">{events.length} Events</span>
          </div>
          <p className="card-subtitle">
            Ordered sequence of synthetic events (newest first). Preserves sequence ordering.
          </p>
        </div>
      </div>

      {highlightedEventId && (
        <div className="highlight-banner">
          <div className="highlight-info">
            <span className="highlight-pin">📍</span>
            <span>Showing all events to reveal evidence: <code>{highlightedEventId}</code></span>
          </div>
          <button type="button" className="btn-clear-highlight" onClick={onClearHighlight}>
            Clear Highlight ✕
          </button>
        </div>
      )}

      <div className="timeline-filters" role="group" aria-label="Filter events timeline">
        <button
          type="button"
          className={`filter-chip ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All ({events.length})
        </button>
        <button
          type="button"
          className={`filter-chip ${filter === 'key' ? 'active' : ''}`}
          onClick={() => setFilter('key')}
        >
          Goals & Shots ({events.filter(e => e.type === 'goal' || e.type === 'shot').length})
        </button>
        <button
          type="button"
          className={`filter-chip ${filter === 'pass' ? 'active' : ''}`}
          onClick={() => setFilter('pass')}
        >
          Passes ({events.filter(e => e.type === 'pass').length})
        </button>
        <button
          type="button"
          className={`filter-chip ${filter === 'recovery' ? 'active' : ''}`}
          onClick={() => setFilter('recovery')}
        >
          Recoveries ({events.filter(e => e.type === 'recovery').length})
        </button>
      </div>

      {filteredEvents.length === 0 ? (
        <p className="timeline-empty">No events match the selected filter.</p>
      ) : (
        <ol className="timeline-list">
          {displayEvents.map(event => {
            const isHighlighted = highlightedEventId === event.event_id;
            const time = formatMatchSecond(event.match_second);
            const team = formatTeamName(event.team_id);
            const type = formatEventType(event.type);
            const outcome = formatOutcome(event.outcome);
            const badgeClass = getEventBadgeClass(event.type);

            return (
              <li
                key={event.event_id}
                id={`event-${event.event_id}`}
                ref={isHighlighted ? highlightedElement : null}
                className={`timeline-item ${isHighlighted ? 'timeline-item-highlighted' : ''}`}
              >
                <div className="timeline-gutter">
                  <span className="timeline-seq">#{event.sequence}</span>
                  <div className="timeline-marker"></div>
                </div>

                <div className="timeline-body">
                  <div className="timeline-item-header">
                    <span className="timeline-time">{time}</span>
                    <span className={`timeline-team team-${event.team_id}`}>{team}</span>
                    <span className={`timeline-badge ${badgeClass}`}>{type}</span>
                    {outcome && (
                      <span className={`timeline-outcome outcome-${event.outcome}`}>{outcome}</span>
                    )}
                  </div>

                  <div className="timeline-item-details">
                    <span className="player-tag">{event.player_id}</span>
                    {typeof event.x === 'number' && (
                      <span className="coord-tag">
                        x: {Math.round(event.x)}{typeof event.end_x === 'number' ? ` → ${Math.round(event.end_x)}` : ''}
                      </span>
                    )}
                    <code className="event-id-tag">{event.event_id}</code>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {!highlightedEventId && filteredEvents.length > 12 && (
        <div className="timeline-expand-bar">
          <button
            type="button"
            className="btn-expand-timeline"
            onClick={() => setShowAll(!showAll)}
          >
            {showAll ? '▲ Show fewer events' : `▼ Show all ${filteredEvents.length} events`}
          </button>
        </div>
      )}
    </section>
  );
}

import React, { useState } from 'react';
import { formatTeamName } from '../utils/formatters';
import { EvidenceList } from './EvidenceList';

export function ShotComparison({ analytics, events = [], onSelectEvent }) {
  const [expandedTeam, setExpandedTeam] = useState(null);
  const shotWindows = analytics?.shot_windows || [];

  const toggleTeam = (teamId) => {
    setExpandedTeam((prev) => (prev === teamId ? null : teamId));
  };

  return (
    <section
      className="dashboard-card shot-comparison-card"
      aria-label="Attacking Activity and Shot Comparison"
    >
      <div className="card-header">
        <div className="header-text-group">
          <div className="title-with-pill">
            <h2 className="card-title">Attacking Activity</h2>
            <span className="feature-pill">5-Min Windows</span>
          </div>
          <p className="card-subtitle">
            Deterministic rule comparing recorded shots between two completed five-minute periods.
          </p>
        </div>
      </div>

      {shotWindows.length === 0 ? (
        <div className="waiting-windows-box">
          <div className="waiting-icon">⏳</div>
          <div className="waiting-text">
            <strong>Waiting for two completed five-minute windows</strong>
            <p>
              The shot comparison rule requires at least 10:00 of recorded match time to compare
              baseline (mins 0–5) against active play (mins 5–10).
            </p>
          </div>
        </div>
      ) : (
        <div className="comparison-grid">
          {shotWindows.map((windowData) => {
            const teamId = windowData.team_id;
            const teamName = formatTeamName(teamId);
            const prev = windowData.previous;
            const curr = windowData.current;
            const diff = curr.shot_count - prev.shot_count;
            const isHome = teamId === 'home';

            // Find max for bar scaling
            const maxVal = Math.max(prev.shot_count, curr.shot_count, 4);
            const prevWidth = Math.round((prev.shot_count / maxVal) * 100);
            const currWidth = Math.round((curr.shot_count / maxVal) * 100);

            const allEvidence = [...prev.evidence_event_ids, ...curr.evidence_event_ids];

            return (
              <div
                key={teamId}
                className={`team-window-card ${isHome ? 'team-home-window' : 'team-away-window'}`}
              >
                <div className="window-team-header">
                  <h3 className="window-team-name">{teamName}</h3>
                  {diff > 0 ? (
                    <span className="window-trend trend-up">
                      +{diff} shots (+{Math.round((diff / (prev.shot_count || 1)) * 100)}%)
                    </span>
                  ) : diff === 0 ? (
                    <span className="window-trend trend-flat">No change</span>
                  ) : (
                    <span className="window-trend trend-down">{diff} shots</span>
                  )}
                </div>

                <div className="window-bars-container">
                  <div className="bar-row">
                    <div className="bar-label-group">
                      <span className="bar-label">
                        Mins {prev.start_second / 60}–{prev.end_second / 60}
                      </span>
                      <strong className="bar-count">
                        {prev.shot_count} {prev.shot_count === 1 ? 'shot' : 'shots'}
                      </strong>
                    </div>
                    <div className="bar-track" aria-hidden="true">
                      <div
                        className="bar-fill bar-fill-prev"
                        style={{ width: `${prevWidth}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="bar-row">
                    <div className="bar-label-group">
                      <span className="bar-label">
                        Mins {curr.start_second / 60}–{curr.end_second / 60}
                      </span>
                      <strong className="bar-count count-highlight">
                        {curr.shot_count} {curr.shot_count === 1 ? 'shot' : 'shots'}
                      </strong>
                    </div>
                    <div className="bar-track" aria-hidden="true">
                      <div
                        className={`bar-fill bar-fill-curr ${diff > 0 ? 'fill-accent' : ''}`}
                        style={{ width: `${currWidth}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="window-footer">
                  <button
                    type="button"
                    className="btn-inspect"
                    onClick={() => toggleTeam(teamId)}
                    aria-expanded={expandedTeam === teamId}
                  >
                    {expandedTeam === teamId
                      ? 'Hide supporting shots ▲'
                      : `Inspect ${allEvidence.length} supporting shots ▼`}
                  </button>

                  {expandedTeam === teamId && (
                    <div className="window-evidence-panel">
                      <div className="evidence-group">
                        <span className="group-label">
                          Mins {prev.start_second / 60}–{prev.end_second / 60} shots:
                        </span>
                        <EvidenceList
                          evidenceIds={prev.evidence_event_ids}
                          events={events}
                          onSelectEvent={onSelectEvent}
                        />
                      </div>
                      <div className="evidence-group">
                        <span className="group-label">
                          Mins {curr.start_second / 60}–{curr.end_second / 60} shots:
                        </span>
                        <EvidenceList
                          evidenceIds={curr.evidence_event_ids}
                          events={events}
                          onSelectEvent={onSelectEvent}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="disclaimer-footnote">
        <span className="disclaimer-icon">ℹ</span>
        <span>
          Recorded shots describe shooting activity; they do not measure possession, dominance, or
          tactical pressure.
        </span>
      </div>
    </section>
  );
}

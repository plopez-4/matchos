import React, { useState } from 'react';
import { EvidenceList } from './EvidenceList';

export function CatchUpPanel({
  summary,
  busy,
  error,
  selectedAudience,
  onAudienceChange,
  onCatchUp,
  events = [],
  onSelectEvent,
}) {
  const [showTrace, setShowTrace] = useState(false);
  const [showRawIds, setShowRawIds] = useState(false);

  const isUpToDate = summary && summary.evidence_event_ids?.length === 0;
  const sections = summary?.explanation?.sections || [];
  const isAzure = summary?.explanation?.mode === 'azure';
  const modelName = summary?.explanation?.model;
  const latency = summary?.explanation?.latency_ms;
  const fallbackReason = summary?.explanation?.fallback_reason;
  const trace = summary?.explanation?.trace || [];

  const getTraceStepLabel = (step) => {
    switch (step.step) {
      case 'get_match_evidence':
        return `Retrieved verified match stories (${step.candidate_count ?? 0} candidates)`;
      case 'verify_selection':
        return `Checked selected stories against available match evidence`;
      case 'complete_coverage':
        return `Included strongest verified shooting-activity change`;
      case 'fallback':
        return `Used deterministic rule-based selection`;
      default:
        return step.step;
    }
  };

  return (
    <section className="dashboard-card catchup-card" aria-label="Catch Me Up AI Briefing">
      <div className="card-header">
        <div className="header-text-group">
          <div className="title-with-pill">
            <h2 className="card-title">Catch Me Up</h2>
            <span className="feature-pill">AI Fan Briefing</span>
          </div>
          <p className="card-subtitle">
            Personalized summary of match events recorded since your last check.
          </p>
        </div>

        {summary && (
          <div
            className="cursor-pill"
            title="Cursor position: events up to this sequence have been summarized"
          >
            Sequence cursor: #{summary.through_sequence}
          </div>
        )}
      </div>

      <div className="audience-toolbar" role="group" aria-label="Select explanation audience style">
        <div
          className="segmented-control"
          role="radiogroup"
          aria-label="Explanation audience style"
        >
          <button
            type="button"
            role="radio"
            aria-checked={selectedAudience === 'casual'}
            className={`segmented-btn ${selectedAudience === 'casual' ? 'active' : ''}`}
            onClick={() => onAudienceChange('casual')}
            disabled={busy}
          >
            Casual Fan
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={selectedAudience === 'advanced'}
            className={`segmented-btn ${selectedAudience === 'advanced' ? 'active' : ''}`}
            onClick={() => onAudienceChange('advanced')}
            disabled={busy}
          >
            Tactical & Advanced
          </button>
        </div>

        <button
          type="button"
          className="btn-primary catchup-cta"
          onClick={onCatchUp}
          disabled={busy}
          aria-busy={busy}
        >
          {busy ? (
            <span className="loading-state">
              <span className="spinner" aria-hidden="true"></span>
              Generating Catch-up…
            </span>
          ) : summary ? (
            'Check for Updates'
          ) : (
            'Catch Me Up'
          )}
        </button>
      </div>

      <div className="audience-help-text">
        {selectedAudience === 'casual' ? (
          <span>
            <strong>Casual:</strong> Clear overview of score changes, goal stories, and high-level
            activity.
          </span>
        ) : (
          <span>
            <strong>Advanced:</strong> Detailed metric comparisons with recorded shot windows and
            defensive recoveries.
          </span>
        )}
      </div>

      {error && (
        <div className="catchup-error-banner" role="alert">
          <div className="error-content">
            <span className="error-icon">⚠️</span>
            <span className="error-text">Failed to fetch catch-up summary: {error}</span>
          </div>
          <button type="button" className="btn-retry" onClick={onCatchUp} disabled={busy}>
            Retry
          </button>
        </div>
      )}

      {/* ARIA live region for Catch Me Up results */}
      <div className="catchup-content-wrap" aria-live="polite">
        {!summary && !busy && (
          <div className="catchup-empty-prompt">
            <div className="prompt-icon">⚽</div>
            <h3>Join the match in progress?</h3>
            <p>
              Click <strong>Catch Me Up</strong> above to analyze all events recorded so far, with
              verified goal stories and shooting activity shifts.
            </p>
          </div>
        )}

        {summary && (
          <div className="catchup-result">
            <div className="result-header-bar">
              <div className="result-mode-badges">
                {isAzure ? (
                  <span
                    className="mode-badge mode-azure"
                    title="Story candidates selected via Azure OpenAI tool calling and verified by backend rules"
                  >
                    <span className="azure-sparkle">✦</span>
                    Selected with Azure AI
                    {modelName && <span className="badge-sub">{modelName}</span>}
                    {typeof latency === 'number' && <span className="badge-sub">{latency}ms</span>}
                  </span>
                ) : (
                  <span
                    className="mode-badge mode-deterministic"
                    title="Story candidates selected deterministically by backend rules"
                  >
                    Evidence-backed rule summary
                    {fallbackReason && fallbackReason !== 'ai_disabled' && (
                      <span className="badge-sub">fallback: {fallbackReason}</span>
                    )}
                  </span>
                )}

                <span className="audience-indicator">
                  Style: <strong>{summary.audience === 'casual' ? 'Casual' : 'Advanced'}</strong>
                  {summary.audience !== selectedAudience && (
                    <span className="audience-mismatch"> (next: {selectedAudience})</span>
                  )}
                </span>
              </div>
            </div>

            {isUpToDate ? (
              <div className="up-to-date-box">
                <span className="checkmark-icon">✓</span>
                <div>
                  <strong>You're completely up to date.</strong>
                  <p>
                    No new recorded events have arrived since your last check (sequence #
                    {summary.through_sequence}).
                  </p>
                </div>
              </div>
            ) : (
              <>
                {summary.intro && (
                  <div className="summary-intro-box">
                    <p className="summary-intro-text">{summary.intro}</p>
                  </div>
                )}

                {sections.length > 0 ? (
                  <div className="sections-grid">
                    {sections.map((section) => (
                      <article key={section.title} className="catchup-section-card">
                        <header className="section-card-header">
                          <h3 className="section-card-title">{section.title}</h3>
                          <span className="evidence-count-pill">
                            {section.evidence_event_ids?.length || 0} events
                          </span>
                        </header>

                        <p className="section-card-text">{section.text}</p>

                        {section.evidence_event_ids?.length > 0 && (
                          <details className="evidence-details">
                            <summary className="evidence-summary-btn">
                              View supporting events ({section.evidence_event_ids.length})
                            </summary>
                            <div className="evidence-content-box">
                              <EvidenceList
                                evidenceIds={section.evidence_event_ids}
                                events={events}
                                onSelectEvent={onSelectEvent}
                              />
                            </div>
                          </details>
                        )}
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="fallback-summary-text">
                    <p>{summary.summary}</p>
                  </div>
                )}
              </>
            )}

            {/* AI Grounding and Transparency Inspector */}
            <div className="grounding-inspector">
              {trace.length > 0 && (
                <div className="inspector-item">
                  <button
                    type="button"
                    className="inspector-toggle"
                    onClick={() => setShowTrace(!showTrace)}
                    aria-expanded={showTrace}
                  >
                    <span>
                      {showTrace ? '▼' : '▶'} AI Selection & Verification Trace ({trace.length}{' '}
                      steps)
                    </span>
                    <span className="toggle-hint">{showTrace ? 'Hide' : 'Inspect'}</span>
                  </button>

                  {showTrace && (
                    <ul className="trace-steps-list">
                      {trace.map((step, idx) => (
                        <li key={idx} className={`trace-step-item status-${step.status}`}>
                          <span className="trace-index">{idx + 1}</span>
                          <div className="trace-details">
                            <span className="trace-label">{getTraceStepLabel(step)}</span>
                            <span className="trace-code">status: {step.status}</span>
                            {step.story_ids && (
                              <span className="trace-meta">
                                stories: {step.story_ids.join(', ')}
                              </span>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              <div className="inspector-item">
                <button
                  type="button"
                  className="inspector-toggle"
                  onClick={() => setShowRawIds(!showRawIds)}
                  aria-expanded={showRawIds}
                >
                  <span>
                    {showRawIds ? '▼' : '▶'} Supporting Event IDs (
                    {summary.evidence_event_ids?.length || 0} new,{' '}
                    {summary.context_evidence_event_ids?.length || 0} context)
                  </span>
                  <span className="toggle-hint">{showRawIds ? 'Hide' : 'Inspect'}</span>
                </button>

                {showRawIds && (
                  <div className="raw-ids-content">
                    <div className="raw-id-group">
                      <strong>New Events in Window:</strong>
                      <p className="code-wrap">
                        {summary.evidence_event_ids?.join(', ') || 'None'}
                      </p>
                    </div>
                    <div className="raw-id-group">
                      <strong>Story Context Events (may include earlier window events):</strong>
                      <p className="code-wrap">
                        {summary.context_evidence_event_ids?.join(', ') || 'None'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

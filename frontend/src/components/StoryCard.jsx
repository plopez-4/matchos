import React, { useState } from 'react';
import { EvidenceList } from './EvidenceList';

export function StoryCard({ stories = [], events = [], onSelectEvent }) {
  const [openEvidence, setOpenEvidence] = useState({});
  const [showTechnical, setShowTechnical] = useState(false);

  const toggleEvidence = (storyId) => {
    setOpenEvidence(prev => ({
      ...prev,
      [storyId]: !prev[storyId],
    }));
  };

  const getStoryKindMeta = (kind) => {
    switch (kind) {
      case 'goal':
        return {
          label: 'Goal Story',
          badgeClass: 'badge-goal',
          icon: '⚽',
        };
      case 'shot_activity':
        return {
          label: 'Attacking Shift',
          badgeClass: 'badge-activity',
          icon: '📈',
        };
      default:
        return {
          label: 'Match Story',
          badgeClass: 'badge-default',
          icon: '📋',
        };
    }
  };

  return (
    <section className="dashboard-card stories-card" aria-label="Match Stories">
      <div className="card-header">
        <div className="header-text-group">
          <div className="title-with-pill">
            <h2 className="card-title">Match Stories</h2>
            <span className="feature-pill">{stories.length} Verified</span>
          </div>
          <p className="card-subtitle">
            Connected narrative units derived by deterministic rules from underlying match events.
          </p>
        </div>

        <button
          type="button"
          className="btn-technical-toggle"
          onClick={() => setShowTechnical(!showTechnical)}
          title="Toggle rule versions and engine IDs"
        >
          {showTechnical ? 'Hide Rule Info' : 'Show Rule Info'}
        </button>
      </div>

      {stories.length === 0 ? (
        <div className="empty-stories-box">
          <p>Run the scenario to see a goal story and a five-minute activity comparison.</p>
        </div>
      ) : (
        <div className="stories-list">
          {stories.map(story => {
            const meta = getStoryKindMeta(story.kind);
            const isOpen = !!openEvidence[story.story_id];
            const evidenceCount = story.evidence_event_ids?.length || 0;

            return (
              <article key={story.story_id} className={`story-item ${meta.badgeClass}-border`}>
                <div className="story-item-top">
                  <span className={`story-badge ${meta.badgeClass}`}>
                    <span className="story-icon">{meta.icon}</span>
                    {meta.label}
                  </span>
                  <span className="story-sequence">Seq #{story.sequence}</span>
                </div>

                <p className="story-text">{story.text}</p>

                {showTechnical && (
                  <div className="story-technical-bar">
                    <span className="tech-tag">rule: {story.rule_version}</span>
                    <span className="tech-tag">id: {story.story_id}</span>
                  </div>
                )}

                <div className="story-actions">
                  <button
                    type="button"
                    className="btn-evidence-toggle"
                    onClick={() => toggleEvidence(story.story_id)}
                    aria-expanded={isOpen}
                  >
                    <span>{isOpen ? '▲ Hide supporting events' : `▼ Inspect supporting events (${evidenceCount})`}</span>
                  </button>
                </div>

                {isOpen && (
                  <div className="story-evidence-drawer">
                    <EvidenceList
                      evidenceIds={story.evidence_event_ids}
                      events={events}
                      onSelectEvent={onSelectEvent}
                    />
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

import React, { useState } from 'react';
import { useMatchData } from '../hooks/useMatchData';
import { ShotComparison } from './ShotComparison';
import { StoryCard } from './StoryCard';
import { EvidenceGraph } from './EvidenceGraph';
import { EventTimeline } from './EventTimeline';

export function DevelopmentInspector({ matchId }) {
  const { data, error } = useMatchData(matchId);
  const [highlighted, setHighlighted] = useState(null);
  return (
    <section className="development-inspector" aria-label="Development match inspector">
      <h2>Match data inspector</h2>
      <p>
        Inspecting <code>{matchId}</code>. These panels use the same recorded events as the fan
        page.
      </p>
      {error && <p role="alert">{error}</p>}
      <ShotComparison
        analytics={data.analytics}
        events={data.events}
        onSelectEvent={setHighlighted}
      />
      <StoryCard stories={data.stories} events={data.events} onSelectEvent={setHighlighted} />
      <EvidenceGraph graph={data.graph} stories={data.stories} />
      <EventTimeline
        events={data.events}
        highlightedEventId={highlighted}
        onClearHighlight={() => setHighlighted(null)}
      />
    </section>
  );
}

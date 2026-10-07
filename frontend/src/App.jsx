import React, { useState, useRef, useCallback, useReducer, useEffect } from 'react';
import { catchUpReducer, initialCatchUpState } from './utils/catchUpState';
import { teamVariables } from './utils/teams';
import { useMatchData } from './hooks/useMatchData';
import { postCatchUp } from './api';
import { MatchHeader } from './components/MatchHeader';
import { Scoreboard } from './components/Scoreboard';
import { CatchUpPanel } from './components/CatchUpPanel';
import { ShotComparison } from './components/ShotComparison';
import { StoryCard } from './components/StoryCard';
import { EventTimeline } from './components/EventTimeline';
import { EvidenceGraph } from './components/EvidenceGraph';
import { SimulatorGuide } from './components/SimulatorGuide';

export function App() {
  const [matchId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('match');
    return requested && /^[a-zA-Z0-9_-]{1,80}$/.test(requested) ? requested : 'demo-match';
  });
  const [{ summary, busy, error: catchUpError }, dispatch] = useReducer(
    catchUpReducer,
    initialCatchUpState,
  );
  const [selectedAudience, setSelectedAudience] = useState('casual');
  const [highlightedEventId, setHighlightedEventId] = useState(null);

  const generationIdRef = useRef(0);
  const requestRef = useRef(null);

  useEffect(
    () => () => {
      generationIdRef.current += 1;
      requestRef.current?.abort();
      requestRef.current = null;
    },
    [],
  );

  // Called when latest sequence drops (e.g. backend restart or simulator re-run)
  const handleReset = useCallback((_newSequence) => {
    generationIdRef.current += 1;
    requestRef.current?.abort();
    requestRef.current = null;
    dispatch({ type: 'reset', generation: generationIdRef.current });
    setHighlightedEventId(null);
  }, []);

  const {
    data,
    status,
    error: pollingError,
    lastUpdated,
  } = useMatchData(matchId, {
    pollInterval: 2000,
    onReset: handleReset,
  });

  const handleCatchUp = async () => {
    if (requestRef.current) return;
    const controller = new AbortController();
    requestRef.current = controller;
    const currentGen = generationIdRef.current;
    const currentCursor = summary?.through_sequence ?? 0;
    dispatch({ type: 'start', generation: currentGen });

    try {
      const result = await postCatchUp(
        matchId,
        {
          since_sequence: currentCursor,
          audience: selectedAudience,
        },
        { signal: controller.signal },
      );

      // Discard stale in-flight response if a backend reset occurred while request was in-flight
      if (currentGen === generationIdRef.current) {
        dispatch({ type: 'success', generation: currentGen, result });
      }
    } catch (err) {
      if (currentGen === generationIdRef.current) {
        // Keep prior summary and cursor intact on failure so retrying doesn't skip events
        dispatch({
          type: 'failure',
          generation: currentGen,
          error: err.message || 'Catch Me Up request failed. Backend may be busy.',
        });
      }
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
    }
  };

  const handleSelectEvent = (eventId) => {
    setHighlightedEventId(eventId);
  };

  const handleClearHighlight = () => {
    setHighlightedEventId(null);
  };

  const hasEvents = data.events.length > 0;

  return (
    <div className="matchos-app" style={teamVariables}>
      <MatchHeader status={status} error={pollingError} lastUpdated={lastUpdated} />

      <main className="dashboard-grid">
        {/* Left Primary Column: Overview, Catch Up, Analytics, Stories, Graph */}
        <div className="main-column">
          <Scoreboard analytics={data.analytics} events={data.events} />

          {!hasEvents && status !== 'loading' && <SimulatorGuide matchId={matchId} />}

          <CatchUpPanel
            summary={summary}
            busy={busy}
            error={catchUpError}
            selectedAudience={selectedAudience}
            onAudienceChange={setSelectedAudience}
            onCatchUp={handleCatchUp}
            events={data.events}
            onSelectEvent={handleSelectEvent}
          />

          <ShotComparison
            analytics={data.analytics}
            events={data.events}
            onSelectEvent={handleSelectEvent}
          />

          <StoryCard
            stories={data.stories}
            events={data.events}
            onSelectEvent={handleSelectEvent}
          />

          <EvidenceGraph graph={data.graph} stories={data.stories} />
        </div>

        {/* Right Secondary Column: Live Timeline of Events */}
        <aside className="sidebar-column">
          <EventTimeline
            events={data.events}
            highlightedEventId={highlightedEventId}
            onClearHighlight={handleClearHighlight}
          />
        </aside>
      </main>

      <footer className="dashboard-footer">
        <div className="footer-content">
          <p className="footer-primary">
            MatchOS — Fictional synthetic replay with deterministic analytics and evidence-linked
            stories.
          </p>
          <p className="footer-secondary">
            AI story selection is powered by Azure OpenAI (<code>matchos-explainer</code>) with
            verified grounding fallback. Displayed metrics and stories come strictly from
            deterministic rules. No real Premier League data used.
          </p>
          <p className="photo-credit">
            Premier League mark: © Copyright The Football Association Premier League Limited, 2016.
          </p>
        </div>
      </footer>
    </div>
  );
}

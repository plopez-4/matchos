import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMatchData, fetchMatchGraph } from '../api';

export function useMatchData(matchId = 'demo-match', options = {}) {
  const { pollInterval = 2000, onReset } = options;

  const [data, setData] = useState({
    events: [],
    stories: [],
    analytics: null,
    graph: null,
  });
  const [status, setStatus] = useState('loading'); // 'loading' | 'connected' | 'stale' | 'empty'
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  const highestSequenceRef = useRef(0);
  const onResetRef = useRef(onReset);
  onResetRef.current = onReset;

  const refresh = useCallback(async (signal) => {
    try {
      const matchResult = await fetchMatchData(matchId, { signal });
      if (signal?.aborted) return;
      const events = matchResult.events || [];
      const latestSequence = events.length > 0 ? (events[events.length - 1]?.sequence ?? 0) : 0;

      // Check if backend was restarted or reset (latest sequence dropped)
      if (highestSequenceRef.current > 0 && latestSequence < highestSequenceRef.current) {
        if (onResetRef.current) {
          onResetRef.current(latestSequence);
        }
      }
      highestSequenceRef.current = latestSequence;

      // Optional graph fetching: try fetching graph if there are events
      let graph = null;
      try {
        if (events.length > 0) {
          graph = await fetchMatchGraph(matchId, { signal });
        }
      } catch {
        // Graph is secondary; don't fail primary data
      }

      if (signal?.aborted) return;
      setData({
        events,
        stories: matchResult.stories || [],
        analytics: matchResult.analytics || null,
        graph,
      });

      setStatus(events.length === 0 ? 'empty' : 'connected');
      setError('');
      setLastUpdated(new Date());
    } catch (err) {
      if (signal?.aborted) return;
      setError(err.message ? `${err.message}. Backend may be offline or restarting.` : 'Connection error');
      setStatus('stale');
    }
  }, [matchId]);

  useEffect(() => {
    let active = true;
    let timerId = null;
    const controller = new AbortController();

    async function poll() {
      if (!active) return;
      await refresh(controller.signal);
      if (active) {
        timerId = setTimeout(poll, pollInterval);
      }
    }

    poll();

    return () => {
      active = false;
      controller.abort();
      if (timerId) clearTimeout(timerId);
    };
  }, [refresh, pollInterval]);

  return {
    data,
    status,
    error,
    lastUpdated,
    refresh,
  };
}

export function visibleTimelineEvents(events, filter, showAll, highlightedEventId) {
  const sorted = [...events].sort((a, b) => b.sequence - a.sequence);
  // Evidence navigation must reveal the target even when a filter or limit hides it.
  if (highlightedEventId && sorted.some(e => e.event_id === highlightedEventId)) return sorted;
  const filtered = sorted.filter(e => filter === 'all'
    || (filter === 'key' ? e.type === 'goal' || e.type === 'shot' : e.type === filter));
  return showAll ? filtered : filtered.slice(0, 12);
}

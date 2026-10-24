import { waitForReplay } from './replay.js';

// A notification is only usable while its own match still has the supported reason.
// Do not tie an already visible notice to the next tick's ranking winner.
export function nextRadarNotice(current, view, dismissed = new Set()) {
  const candidate = view?.notification;
  const notice = candidate && !dismissed.has(candidate.id) ? candidate : current;
  if (!notice || dismissed.has(notice.id)) return null;
  const entry = view?.matches.find((item) => item.match_id === notice.match_id);
  const reason = entry?.pulse?.why_now;
  if (
    !entry?.pulse?.eligible ||
    !reason ||
    view.finished ||
    view.clock_second >= reason.expires_at_second
  )
    return null;
  return { ...notice, entry, reason };
}

// A running tab can receive an older server response during a restart.
export function discoveryReason(entry, now = 0) {
  if (!entry) return null;
  const reason = entry.pulse?.why_now;
  if (reason?.headline && reason?.text) {
    return { ...reason, evidence_event_ids: reason.evidence_event_ids ?? [] };
  }
  return {
    headline: `${entry.home} vs ${entry.away}`,
    text: entry.pulse?.reason ?? 'Follow this match to see the recorded events.',
    observed_second: now,
    evidence_event_ids: entry.pulse?.evidence_event_ids ?? [],
  };
}

// Keep failed releases until recovery; never accumulate abandoned replay groups.
export function createReleaseRecovery(release) {
  let pending;
  return {
    queue(id) {
      if (pending && pending !== id) throw new Error('Previous matchday cleanup is still pending');
      pending = id;
    },
    async retry(options = {}) {
      if (!pending) return;
      const id = pending;
      try {
        const deadline = AbortSignal.timeout(10000);
        const signal = options.signal ? AbortSignal.any([options.signal, deadline]) : deadline;
        await release(id, { ...options, signal });
      } catch (error) {
        if (![401, 403, 404].includes(error.status)) throw error;
      }
      if (!options.signal?.aborted && pending === id) pending = undefined;
    },
  };
}

// One request at a time; an aborted request may still have committed a tick.
// Retrying that tick is safe and returns the same shared clock snapshot.
export async function playMatchday({ initialView, intervalMs, signal, step, onView }) {
  let current = initialView;
  while (!current.finished && !signal.aborted) {
    await waitForReplay(intervalMs, signal);
    if (signal.aborted) return false;
    const next = await step(current.matchday_id, current.tick + 1, { signal });
    if (signal.aborted) return false;
    current = next;
    onView(next);
  }
  return !signal.aborted;
}

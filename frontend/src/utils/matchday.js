import { waitForReplay } from './replay.js';

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

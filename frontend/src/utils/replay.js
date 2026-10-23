export function waitForReplay(ms, signal) {
  return new Promise((resolve) => {
    if (signal.aborted) return resolve();
    const finish = () => {
      clearTimeout(timer);
      signal.removeEventListener('abort', finish);
      resolve();
    };
    const timer = setTimeout(finish, ms);
    signal.addEventListener('abort', finish, { once: true });
  });
}

// Requests run in sequence. A cancelled request may have reached the server;
// retrying the same event is safe because ingestion is idempotent.
export async function playReplay({
  events,
  startIndex,
  intervalMs,
  signal,
  ingest,
  onProgress,
  wait = waitForReplay,
}) {
  for (let index = startIndex; index < events.length; index += 1) {
    await wait(intervalMs, signal);
    if (signal.aborted) return false;
    await ingest(events[index], { signal });
    if (signal.aborted) return false;
    onProgress(index + 1);
  }
  return true;
}

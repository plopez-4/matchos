// getRandomValues also works on private-network HTTP origins used for phone tests.
export function replayId(prefix = 'day', cryptoApi = globalThis.crypto) {
  const bytes = cryptoApi.getRandomValues(new Uint8Array(16));
  return `${prefix}-${Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')}`;
}

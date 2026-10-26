// Resolve availability before playback; provider errors never switch voices silently.
export function narratorVoice(preference, cloudAvailable) {
  return preference === 'auto' ? (cloudAvailable ? 'matchday' : 'device') : preference;
}

export function narrationRate(value) {
  return Number(value) === 0.75 ? 0.75 : 1;
}

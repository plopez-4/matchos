// Resolve availability before playback; provider errors never switch voices silently.
export function narratorVoice(preference, cloudAvailable) {
  return preference === 'auto' ? (cloudAvailable ? 'matchday' : 'device') : preference;
}

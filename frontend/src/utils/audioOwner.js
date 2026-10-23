let owner;
export function claimAudio(stop) {
  owner?.();
  owner = stop;
}
export function ownsAudio(stop) {
  return owner === stop;
}
export function releaseAudio(stop) {
  if (owner === stop) owner = undefined;
}

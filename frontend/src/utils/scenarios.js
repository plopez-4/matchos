export const VALID_SCENARIOS = [
  'pressure-builds',
  'comeback',
  'quiet-match',
  'legacy-default',
  'united-city-90',
  'united-hull-90',
];
export const DEFAULT_SCENARIO = 'pressure-builds';

export function resolveScenario(param) {
  return VALID_SCENARIOS.includes(param) ? param : DEFAULT_SCENARIO;
}

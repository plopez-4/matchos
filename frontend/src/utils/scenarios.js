export const VALID_SCENARIOS = ['pressure-builds', 'comeback', 'quiet-match', 'legacy-default'];
export const DEFAULT_SCENARIO = 'pressure-builds';

export function resolveScenario(param) {
  return VALID_SCENARIOS.includes(param) ? param : DEFAULT_SCENARIO;
}

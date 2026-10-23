import fixtures from '../../../backend/app/data/demo_fixtures.json' with { type: 'json' };

export const DEMO_FIXTURES = fixtures;
export const VALID_SCENARIOS = fixtures.map((fixture) => fixture.id);
export const DEFAULT_SCENARIO = 'united-city-90';

export function resolveScenario(param) {
  return VALID_SCENARIOS.includes(param) ? param : DEFAULT_SCENARIO;
}

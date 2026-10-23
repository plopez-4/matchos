import test from 'node:test';
import assert from 'node:assert/strict';
import { DEMO_FIXTURES, resolveScenario } from '../src/utils/scenarios.js';
import { teamsForScenario, variablesForTeams } from '../src/utils/teams.js';

test('both experiences present the shared current fixtures without placeholder teams', () => {
  assert.equal(DEMO_FIXTURES.length, 3);
  for (const fixture of DEMO_FIXTURES) {
    assert.equal(resolveScenario(fixture.id), fixture.id);
    const teams = teamsForScenario(fixture.id);
    assert.equal(teams.home.name, fixture.home);
    assert.equal(teams.away.name, fixture.away);
    assert.equal(variablesForTeams(teams)['--team-away'], teams.away.color);
    assert.ok(teams.home.color && teams.away.color);
  }
  assert.equal(teamsForScenario('united-hull-90').away.name, 'Manchester City');
});

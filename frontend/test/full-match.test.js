import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveScenario } from '../src/utils/scenarios.js';
import { teamsForScenario, variablesForTeams } from '../src/utils/teams.js';

test('full-match URLs resolve to their actual team presentation', () => {
  for (const id of ['united-city-90', 'united-hull-90']) {
    assert.equal(resolveScenario(id), id);
    const teams = teamsForScenario(id);
    assert.equal(teams.home.name, 'Manchester United');
    assert.equal(teams.home.color, '#ef3340');
    assert.equal(teams.away.name, id === 'united-city-90' ? 'Manchester City' : 'Hull City');
    assert.equal(variablesForTeams(teams)['--team-away'], teams.away.color);
  }
  assert.equal(teamsForScenario('legacy-default').home.name, 'Home FC');
});

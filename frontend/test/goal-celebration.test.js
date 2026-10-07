import test from 'node:test';
import assert from 'node:assert/strict';
import { newScoringTeams, teams, teamVariables } from '../src/utils/teams.js';

test('opening an already scored match does not celebrate an old goal', () => {
  assert.deepEqual(newScoringTeams(null, { home: 1, away: 0 }), []);
});
test('score changes identify the scoring team and unchanged polls do not repeat', () => {
  assert.deepEqual(newScoringTeams({ home: 0, away: 0 }, { home: 1, away: 0 }), ['home']);
  assert.deepEqual(newScoringTeams({ home: 1, away: 0 }, { home: 1, away: 1 }), ['away']);
  assert.deepEqual(newScoringTeams({ home: 1, away: 1 }, { home: 1, away: 1 }), []);
});
test('score rollback does not celebrate; multiple goals are queued', () => {
  assert.deepEqual(newScoringTeams({ home: 2, away: 1 }, { home: 0, away: 0 }), []);
  assert.deepEqual(newScoringTeams({ home: 0, away: 0 }, { home: 2, away: 1 }), [
    'home',
    'home',
    'away',
  ]);
});
test('kit colors are shared by team presentation and the scoreboard takeover', () => {
  assert.equal(teamVariables['--team-home'], teams.home.color);
  assert.equal(teamVariables['--team-away'], teams.away.color);
  assert.equal(teams.home.kit, 'White');
  assert.equal(teams.away.kit, 'Red');
});

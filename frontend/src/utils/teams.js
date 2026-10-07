// Presentation metadata for the fictional replay. Change kits here for another fixture.
export const teams = {
  home: { name: 'Home FC', kit: 'White', color: '#ffffff', ink: '#37003c' },
  away: { name: 'Away FC', kit: 'Red', color: '#ef3340', ink: '#ffffff' },
};

export const teamVariables = Object.fromEntries(
  Object.entries(teams).flatMap(([id, team]) => [
    [`--team-${id}`, team.color],
    [`--team-${id}-ink`, team.ink],
  ]),
);

export function teamsForScenario(id) {
  if (!['united-city-90', 'united-hull-90'].includes(id)) return teams;
  return {
    home: { name: 'Manchester United', short: 'UTD', kit: 'Red', color: '#ef3340', ink: '#ffffff' },
    away:
      id === 'united-city-90'
        ? {
            name: 'Manchester City',
            short: 'CITY',
            kit: 'Sky blue',
            color: '#6cabdd',
            ink: '#182534',
          }
        : { name: 'Hull City', short: 'HULL', kit: 'Amber', color: '#f4a900', ink: '#182534' },
  };
}

export function variablesForTeams(fixtureTeams) {
  return Object.fromEntries(
    Object.entries(fixtureTeams).flatMap(([id, team]) => [
      [`--team-${id}`, team.color],
      [`--team-${id}-ink`, team.ink],
    ]),
  );
}

export function newScoringTeams(previous, current) {
  if (!previous || !current) return [];
  // A lower score is a reset/correction, never a new goal.
  if (current.home < previous.home || current.away < previous.away) return [];
  return ['home', 'away'].flatMap((id) =>
    Array.from({ length: Math.max(0, current[id] - previous[id]) }, () => id),
  );
}

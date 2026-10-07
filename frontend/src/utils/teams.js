// Presentation metadata for the fictional replay. Change kits here for another fixture.
export const teams = {
  home: { name: 'Home FC', kit: 'White', color: '#ffffff', ink: '#37003c' },
  away: { name: 'Away FC', kit: 'Red', color: '#ef3340', ink: '#ffffff' },
};

export const teamVariables = Object.fromEntries(Object.entries(teams).flatMap(([id, team]) => [
  [`--team-${id}`, team.color], [`--team-${id}-ink`, team.ink],
]));

export function newScoringTeams(previous, current) {
  if (!previous || !current) return [];
  // A lower score is a reset/correction, never a new goal.
  if (current.home < previous.home || current.away < previous.away) return [];
  return ['home', 'away'].flatMap(id => Array.from({ length: Math.max(0, current[id] - previous[id]) }, () => id));
}

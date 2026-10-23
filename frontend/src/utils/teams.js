import { DEMO_FIXTURES } from './scenarios.js';

// 2026–27 club names; representative home-kit colors, not official brand specifications.
export const clubs = [
  { id: 'arsenal', name: 'Arsenal', short: 'ARS', color: '#ef3340', ink: '#ffffff' },
  { id: 'aston-villa', name: 'Aston Villa', short: 'AVL', color: '#7a263a', ink: '#ffffff' },
  { id: 'bournemouth', name: 'AFC Bournemouth', short: 'BOU', color: '#da291c', ink: '#ffffff' },
  { id: 'brentford', name: 'Brentford', short: 'BRE', color: '#e30613', ink: '#ffffff' },
  {
    id: 'brighton',
    name: 'Brighton & Hove Albion',
    aliases: ['Brighton'],
    short: 'BHA',
    color: '#0057b8',
    ink: '#ffffff',
  },
  { id: 'chelsea', name: 'Chelsea', short: 'CHE', color: '#034694', ink: '#ffffff' },
  { id: 'crystal-palace', name: 'Crystal Palace', short: 'CRY', color: '#1b458f', ink: '#ffffff' },
  { id: 'coventry', name: 'Coventry City', short: 'COV', color: '#6caddf', ink: '#182534' },
  { id: 'everton', name: 'Everton', short: 'EVE', color: '#003399', ink: '#ffffff' },
  { id: 'fulham', name: 'Fulham', short: 'FUL', color: '#ffffff', ink: '#182534' },
  { id: 'hull', name: 'Hull City', short: 'HUL', color: '#f4a900', ink: '#182534' },
  { id: 'ipswich', name: 'Ipswich Town', short: 'IPS', color: '#0057b8', ink: '#ffffff' },
  { id: 'leeds', name: 'Leeds United', short: 'LEE', color: '#ffffff', ink: '#182534' },
  { id: 'liverpool', name: 'Liverpool', short: 'LIV', color: '#c8102e', ink: '#ffffff' },
  {
    id: 'manchester-city',
    name: 'Manchester City',
    short: 'MCI',
    color: '#6cabdd',
    ink: '#182534',
  },
  {
    id: 'manchester-united',
    name: 'Manchester United',
    short: 'MUN',
    color: '#ef3340',
    ink: '#ffffff',
  },
  { id: 'newcastle', name: 'Newcastle United', short: 'NEW', color: '#ffffff', ink: '#182534' },
  {
    id: 'nottingham-forest',
    name: 'Nottingham Forest',
    short: 'NFO',
    color: '#dd0000',
    ink: '#ffffff',
  },
  { id: 'sunderland', name: 'Sunderland', short: 'SUN', color: '#eb172b', ink: '#ffffff' },
  { id: 'tottenham', name: 'Tottenham Hotspur', short: 'TOT', color: '#ffffff', ink: '#182534' },
];

export const clubByName = (name) =>
  clubs.find((club) => club.name === name || club.aliases?.includes(name)) ?? null;

// Both experiences use the same fixture manifest and roster identities.
export function teamsForScenario(id) {
  const fixture = DEMO_FIXTURES.find((item) => item.id === id) ?? DEMO_FIXTURES[0];
  return Object.fromEntries(
    ['home', 'away'].map((side) => {
      const club = clubByName(fixture[side]);
      return [
        side,
        {
          ...club,
          name: fixture[side],
          kit:
            {
              'manchester-united': 'Red',
              'manchester-city': 'Sky blue',
              'crystal-palace': 'Red and blue',
              newcastle: 'Black and white',
              brighton: 'Blue and white',
              fulham: 'White',
            }[club?.id] ?? 'Home colors',
        },
      ];
    }),
  );
}

export const teams = teamsForScenario(DEMO_FIXTURES[0].id);
export const teamVariables = Object.fromEntries(
  Object.entries(teams).flatMap(([id, team]) => [
    [`--team-${id}`, team.color],
    [`--team-${id}-ink`, team.ink],
  ]),
);

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

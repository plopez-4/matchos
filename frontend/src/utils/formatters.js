export function formatMatchSecond(second) {
  if (typeof second !== 'number' || isNaN(second)) return '0:00';
  const mins = Math.floor(second / 60);
  const secs = second % 60;
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

export function formatTeamName(teamId) {
  if (teamId === 'home') return 'Home FC';
  if (teamId === 'away') return 'Away FC';
  return teamId ? teamId.toUpperCase() : 'Unknown';
}

export function formatEventType(type) {
  switch (type) {
    case 'kickoff':
      return 'Kickoff';
    case 'pass':
      return 'Pass';
    case 'shot':
      return 'Shot';
    case 'goal':
      return 'Goal';
    case 'recovery':
      return 'Recovery';
    default:
      return type ? type.charAt(0).toUpperCase() + type.slice(1) : '';
  }
}

export function formatOutcome(outcome) {
  if (!outcome) return null;
  switch (outcome) {
    case 'complete':
      return 'Complete';
    case 'saved':
      return 'Saved';
    case 'blocked':
      return 'Blocked';
    case 'missed':
      return 'Missed';
    case 'goal':
      return 'Goal';
    default:
      return outcome;
  }
}

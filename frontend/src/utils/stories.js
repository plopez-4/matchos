export function getStoryKindMeta(kind) {
  switch (kind) {
    case 'goal':
      return {
        label: 'Goal Story',
        badgeClass: 'badge-goal',
        icon: '⚽',
      };
    case 'shot_activity':
      return {
        label: 'Attacking Shift',
        badgeClass: 'badge-activity',
        icon: '📈',
      };
    case 'high_recovery':
      return {
        label: 'High Recovery',
        badgeClass: 'badge-recovery',
        icon: '🛡️',
      };
    case 'progressive_pass':
      return {
        label: 'Progressive Pass',
        badgeClass: 'badge-pass',
        icon: '⚡',
      };
    case 'recovery_shot':
      return {
        label: 'Recovery to Shot',
        badgeClass: 'badge-transition',
        icon: '⏱️',
      };
    default:
      return {
        label: 'Match Story',
        badgeClass: 'badge-default',
        icon: '📋',
      };
  }
}

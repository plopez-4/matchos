import reasons from '../../../backend/app/data/sending_off_reasons.json' with { type: 'json' };

export function sendingOffDetails(card, events = [], language = 'en') {
  const es = language === 'es';
  const post = card.card_phase === 'post_match';
  const clock = `${Math.floor(card.match_second / 60)}:${String(card.match_second % 60).padStart(2, '0')}`;
  const count = new Set(
    events
      .filter(
        (event) =>
          event.type === 'red_card' &&
          event.card_phase !== 'post_match' &&
          event.team_id === card.team_id &&
          event.sequence <= card.sequence,
      )
      .map((event) => event.player_id),
  ).size;
  const remaining = 11 - count;
  return {
    heading: `${card.player_name || card.player_id} · ${post ? (es ? 'Después del pitido final' : 'After full time') : clock}`,
    reason:
      reasons[card.card_reason]?.[language] ??
      (es
        ? 'El motivo de la expulsión no consta en los datos.'
        : 'The reason for the dismissal is not recorded.'),
    consequence: post
      ? es
        ? 'Esta expulsión posterior al partido no cambió el resultado ni el número de jugadores durante el encuentro.'
        : 'This post-match dismissal did not change the result or the playing numbers during the match.'
      : es
        ? `${card.team_name || card.team_id} quedó con ${remaining} jugadores.`
        : `${card.team_name || card.team_id} were reduced to ${remaining} players.`,
    clock,
    post,
  };
}

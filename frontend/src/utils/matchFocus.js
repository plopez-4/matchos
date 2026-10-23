import { pitchMoves } from './pitchReplay.js';
import { recapText } from './speechRecap.js';

export function featuredMoment(events = [], preferGoal = true) {
  const playable = pitchMoves(events).flatMap((move) => move.events);
  const newest = (type) => [...playable].reverse().find((event) => event.type === type);
  return (preferGoal ? newest('goal') : null) ?? newest('shot') ?? newest('goal') ?? null;
}

export function alertMoment(entry) {
  const goalTrigger = entry?.pulse?.why_now?.trigger !== 'shot_activity';
  return featuredMoment(entry?.pulse?.evidence_events ?? [], goalTrigger);
}

export function momentTitle(event, briefing) {
  if (!event) return 'Follow the match.';
  const team = event.team_name || (event.team_id === 'home' ? 'Home' : 'Away');
  if (event.type !== 'goal') return `${team}: a chance to revisit.`;
  const transition = briefing?.trajectory?.transitions?.find(
    (step) => step.sequence === event.sequence,
  );
  const wording = {
    equalization: 'draw level',
    lead_acquisition: 'take the lead',
    lead_reversal: 'turn the lead around',
    lead_extension: 'extend their lead',
    deficit_reduction: 'pull a goal back',
  };
  return `${team} ${wording[transition?.type] ?? 'score'}.`;
}

export function matchRecap(briefing, language = 'en') {
  // The writer already supplies a concise paragraph. Cutting by sentence count
  // discards the activity, response interval and current situation it explains.
  return recapText(briefing, language).trim();
}

export function retainCatchUp(previous, result) {
  // An empty check has no new prose. Keep the last explanation, with its original
  // snapshot time, while the caller explicitly reports that there is no update.
  if (result.evidence_event_ids?.length === 0 && previous?.fan_briefing) {
    return {
      ...result,
      fan_briefing: previous.fan_briefing,
      explanation: previous.explanation ?? result.explanation,
    };
  }
  return result;
}

export function contributionReplayMoments(briefing, events = []) {
  const plan = briefing?.story_plan;
  const primary = plan?.stories?.find((item) => item.story_id === plan.change_story_id);
  const link = primary?.metric?.goal_link;
  if (link && briefing.snapshot) {
    const sources = new Set(primary.evidence_event_ids);
    const scoped = events.filter(
      (event) =>
        sources.has(event.event_id) && event.sequence <= briefing.snapshot.through_sequence,
    );
    const shot = scoped.find((event) => event.event_id === primary.metric.shot_event_id);
    const goal = scoped.find((event) => event.event_id === link.goal_event_id);
    const playable = pitchMoves(events).some((move) =>
      move.events.some((event) => event.event_id === goal?.event_id),
    );
    return shot?.type === 'shot' &&
      shot.outcome === 'goal' &&
      goal?.type === 'goal' &&
      goal.related_event_id === shot.event_id &&
      goal.team_id === shot.team_id &&
      goal.player_id === shot.player_id &&
      goal.period === shot.period &&
      goal.possession_id === shot.possession_id &&
      playable
      ? [goal]
      : [];
  }
  const story = plan?.stories?.find((item) => item.story_id === plan.player_story_id);
  if (!story || !briefing.snapshot) return [];
  const sources = new Set(story.evidence_event_ids);
  const playable = new Set(
    pitchMoves(events).flatMap((move) => move.events.map((event) => event.event_id)),
  );
  const available = events.filter(
    (event) =>
      sources.has(event.event_id) &&
      event.sequence <= briefing.snapshot.through_sequence &&
      playable.has(event.event_id),
  );
  const byId = new Map(available.map((event) => [event.event_id, event]));
  if (story.kind === 'player_shot_creation') {
    return (story.metric.links ?? []).flatMap((link) => {
      const pass = byId.get(link.pass_event_id);
      const shot = byId.get(link.shot_event_id);
      return pass &&
        shot &&
        pass.type === 'pass' &&
        pass.outcome === 'complete' &&
        shot.type === 'shot' &&
        pass.player_id === story.metric.player_id &&
        pass.recipient_player_id === shot.player_id &&
        pass.possession_id === shot.possession_id &&
        pass.team_id === shot.team_id &&
        pass.period === shot.period
        ? [shot]
        : [];
    });
  }
  return available.filter(
    (event) =>
      event.player_id === story.metric.player_id &&
      event.type === (story.kind === 'player_shooting' ? 'shot' : 'pass'),
  );
}

export function recapReplayLabel(event, briefing, language = 'en') {
  const es = language === 'es';
  const name = event.player_name || (es ? 'jugador' : 'player');
  if (event.type === 'goal') {
    const equalizer = briefing?.trajectory?.transitions?.some(
      (step) => step.sequence === event.sequence && step.type === 'equalization',
    );
    return es
      ? `Ver el gol${equalizer ? ' del empate' : ''} de ${name}`
      : `Watch ${name}’s ${equalizer ? 'equalizer' : 'goal'}`;
  }
  const action =
    event.type === 'pass'
      ? es
        ? 'Pase'
        : 'Pass'
      : event.outcome === 'saved'
        ? es
          ? 'Remate detenido'
          : 'Saved shot'
        : event.outcome === 'goal'
          ? es
            ? 'Remate de gol'
            : 'Goal attempt'
          : es
            ? 'Remate'
            : 'Shot';
  return `${action} · ${name}`;
}

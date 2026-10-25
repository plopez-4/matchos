import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';
import {
  featuredMoment,
  alertMoment,
  momentTitle,
  matchRecap,
  retainCatchUp,
  contributionReplayMoments,
  recapReplayLabel,
} from '../src/utils/matchFocus.js';

test('linked scoring action replays the exact equalizer and rejects missing or future evidence', () => {
  const scope = {
    match_id: 'm',
    period: 2,
    team_id: 'home',
    possession_id: 'p',
    player_id: 'h9',
    player_name: 'Ismaila Sarr',
    x: 82,
    y: 50,
  };
  const shot = {
    ...scope,
    event_id: 's',
    sequence: 3,
    type: 'shot',
    outcome: 'goal',
    match_second: 3610,
    end_x: 100,
    end_y: 50,
  };
  const goal = {
    ...scope,
    event_id: 'g',
    sequence: 4,
    type: 'goal',
    related_event_id: 's',
    match_second: 3611,
  };
  const story = {
    story_id: 'transition',
    kind: 'recovery_shot',
    evidence_event_ids: ['s', 'g'],
    metric: { shot_event_id: 's', goal_link: { goal_event_id: 'g' } },
  };
  const briefing = {
    snapshot: { through_sequence: 4 },
    trajectory: { transitions: [{ sequence: 4, type: 'equalization' }] },
    story_plan: { change_story_id: 'transition', stories: [story] },
  };
  assert.deepEqual(contributionReplayMoments(briefing, [shot, goal]), [goal]);
  assert.equal(recapReplayLabel(goal, briefing, 'en'), 'Watch Ismaila Sarr’s equalizer');
  assert.equal(recapReplayLabel(goal, briefing, 'es'), 'Ver el gol del empate de Ismaila Sarr');
  assert.deepEqual(contributionReplayMoments(briefing, [goal]), []);
  assert.deepEqual(
    contributionReplayMoments({ ...briefing, snapshot: { through_sequence: 3 } }, [shot, goal]),
    [],
  );
  assert.deepEqual(
    contributionReplayMoments(briefing, [shot, { ...goal, related_event_id: 'other' }]),
    [],
  );
  assert.equal(
    recapReplayLabel({ ...shot, outcome: 'saved' }, briefing, 'en'),
    'Saved shot · Ismaila Sarr',
  );
});

const event = (sequence, type, fields = {}) => ({
  event_id: `e${sequence}`,
  sequence,
  match_id: 'm',
  period: 2,
  team_id: 'home',
  team_name: 'Palace',
  player_id: 'h9',
  type,
  match_second: 4500 + sequence,
  x: 80,
  y: 50,
  end_x: 100,
  end_y: 50,
  ...fields,
});

test('goal alerts select the promised goal instead of a later ordinary action', () => {
  const events = [event(1, 'shot'), event(2, 'goal'), event(3, 'pass'), event(4, 'shot')];
  const entry = { pulse: { why_now: { trigger: 'equalizer' }, evidence_events: events } };
  assert.equal(alertMoment(entry).event_id, 'e2');
  entry.pulse.why_now.trigger = 'shot_activity';
  assert.equal(alertMoment(entry).event_id, 'e4');
  entry.pulse.why_now = null;
  assert.equal(alertMoment(entry).event_id, 'e2');
  assert.equal(featuredMoment(events).event_id, 'e2');
  assert.equal(featuredMoment([event(1, 'pass')]), null);
  assert.equal(alertMoment(null), null);
});

test('red card alerts select the red card event and moment title describes it', () => {
  const events = [
    event(1, 'pass'),
    event(2, 'red_card', { player_name: 'Elliot Anderson' }),
    event(3, 'shot'),
  ];
  const entry = { pulse: { why_now: { trigger: 'red_card' }, evidence_events: events } };
  assert.equal(alertMoment(entry).event_id, 'e2');
  assert.equal(momentTitle(events[1]), 'Elliot Anderson: red card shown.');
  assert.equal(featuredMoment(events).event_id, 'e2');
});

test('moment titles describe the selected historical goal using its own transition', () => {
  const briefing = {
    trajectory: {
      transitions: [
        { sequence: 2, type: 'equalization' },
        { sequence: 4, type: 'lead_reversal' },
      ],
    },
  };
  assert.equal(momentTitle(event(2, 'goal'), briefing), 'Palace draw level.');
  assert.equal(momentTitle(event(4, 'goal'), briefing), 'Palace turn the lead around.');
  assert.equal(momentTitle(event(1, 'shot'), briefing), 'Palace: a chance to revisit.');
});

test('recap preserves the story and supporting context beyond the first two sentences', () => {
  assert.equal(matchRecap(null), '');
  const briefing = {
    spoken_recap: { en: 'Palace are level. Newcastle led twice. There are six recent shots.' },
  };
  assert.equal(
    matchRecap(briefing),
    'Palace are level. Newcastle led twice. There are six recent shots.',
  );
});

test('an empty catch-up preserves the previous explanation and its snapshot, not an invented fresh recap', () => {
  const previous = {
    explanation: { sections: [{ title: 'What changed', text: 'Recorded shots increased.' }] },
    fan_briefing: {
      clock: '75:30',
      spoken_recap: { en: 'Palace are level. Six shots in the last five minutes.' },
    },
    through_sequence: 80,
  };
  const result = { fan_briefing: null, through_sequence: 80, evidence_event_ids: [] };
  const retained = retainCatchUp(previous, result);
  assert.equal(retained.fan_briefing, previous.fan_briefing);
  assert.equal(retained.fan_briefing.clock, '75:30');
  assert.equal(retained.explanation, previous.explanation);
  assert.deepEqual(retained.evidence_event_ids, []);
  const changed = {
    fan_briefing: { clock: '76:00' },
    through_sequence: 85,
    evidence_event_ids: ['e85'],
  };
  assert.equal(retainCatchUp(previous, changed), changed);
});

const bundle = await build({
  entryPoints: {
    recap: 'src/components/FocusedRecap.jsx',
    pitch: 'src/components/PitchReplay.jsx',
    app: 'src/App.jsx',
    inspector: 'src/components/DevelopmentInspector.jsx',
  },
  outdir: 'unused',
  bundle: true,
  write: false,
  platform: 'node',
  format: 'esm',
  external: ['react', 'react-dom'],
  loader: { '.css': 'empty' },
});
async function component(name) {
  const source = bundle.outputFiles
    .find((file) => file.path.endsWith(`${name}.js`))
    .text.replaceAll('from "react"', `from ${JSON.stringify(import.meta.resolve('react'))}`)
    .replaceAll('from "react-dom"', `from ${JSON.stringify(import.meta.resolve('react-dom'))}`);
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
}
const { FocusedRecap } = await component('recap');
const { PitchReplay } = await component('pitch');
const { App } = await component('app');
const { DevelopmentInspector } = await component('inspector');

test('a capacity fallback stays labeled as recorded events in both languages', () => {
  const briefing = {
    clock: '62:30',
    evidence_event_ids: [],
    spoken_recap: { en: 'The score is level.', es: 'El marcador está empatado.' },
    narrative: { mode: 'deterministic', fallback_reason: 'provider_cooldown' },
  };
  for (const [language, label] of [
    ['en', 'AI temporarily busy'],
    ['es', 'IA temporalmente ocupada'],
  ]) {
    const html = renderToStaticMarkup(React.createElement(FocusedRecap, { briefing, language }));
    assert.match(html, new RegExp(label));
    assert.doesNotMatch(html, /AI-written recap|Resumen con IA|provider_cooldown/);
  }
});

test('focused recap keeps evidence accessible without experimental controls or duplicate sections', () => {
  const briefing = {
    clock: '75:30',
    evidence_event_ids: ['e2'],
    spoken_recap: { en: 'Palace are level. Newcastle led twice. Six recent shots.' },
  };
  const html = renderToStaticMarkup(
    React.createElement(FocusedRecap, { briefing, events: [event(2, 'goal')] }),
  );
  assert.match(html, /Palace are level. Newcastle led twice./);
  assert.match(html, /Six recent shots/);
  assert.match(html, /Inspect supporting events/);
  assert.doesNotMatch(html, /Broadcast Mode|Preview voice|Historical precedent|Sequence cursor/);
  assert.match(html, /Listen to recap/);
  assert.match(html, /Voice options/);
});

test('catch-up exposes grounded changes on demand and explicitly reports a quiet repeat check', () => {
  const briefing = {
    clock: '75:30',
    snapshot: { since_sequence: 70 },
    evidence_event_ids: ['e2'],
    spoken_recap: { en: 'Palace are level. Six recent shots.' },
  };
  const summary = {
    evidence_event_ids: ['e2'],
    explanation: {
      sections: [
        {
          title: 'What changed',
          text: 'Recorded shot activity increased.',
          evidence_event_ids: ['e2'],
        },
      ],
    },
  };
  const html = renderToStaticMarkup(
    React.createElement(FocusedRecap, { briefing, summary, events: [event(2, 'shot')] }),
  );
  assert.match(html, /Since your last catch-up/);
  assert.match(html, /Recorded shot activity increased/);
  assert.match(html, /<details class="focus-evidence">/);
  const quiet = renderToStaticMarkup(
    React.createElement(FocusedRecap, { briefing, summary: { evidence_event_ids: [] } }),
  );
  assert.match(quiet, /No new recorded action since your last check/);
  assert.match(quiet, /Palace are level. Six recent shots./);
});

test('compact pitch keeps playback and hides the permanent wall of moment buttons', () => {
  const html = renderToStaticMarkup(
    React.createElement(PitchReplay, { compact: true, events: [event(1, 'shot')] }),
  );
  assert.match(html, /Pause replay/);
  assert.match(html, /<summary>Earlier moments<\/summary>/);
  assert.doesNotMatch(html, /Move speed|Replay this move|Follow the move\./);
});

test('the default route is the branded main page and development is explicit', () => {
  const previous = globalThis.window;
  try {
    globalThis.window = { location: { search: '' } };
    const main = renderToStaticMarkup(React.createElement(App));
    assert.match(main, /stadium-hero/);
    assert.match(main, /Premier League/);
    assert.match(main, /Microsoft Azure/);
    assert.match(main, /Manchester United/);
    assert.match(main, /Manchester City/);
    assert.doesNotMatch(
      main,
      /Hull City|Home FC|Away FC|Match Highlights Timeline|Match Story Graph|Attacking Activity|Sequence cursor|Broadcast Mode/,
    );
    assert.match(main, /Catch Me Up/);
    assert.match(main, /Demo settings/);
    assert.match(main, /All three matches run together/);
    assert.match(main, /Crystal Palace vs Newcastle United/);
    assert.match(main, /Brighton vs Fulham/);
    const inspector = renderToStaticMarkup(
      React.createElement(DevelopmentInspector, { matchId: 'same-fan-match' }),
    );
    assert.match(inspector, /same-fan-match/);
    assert.match(inspector, /Match Highlights Timeline/);
    assert.match(inspector, /Match Story Graph/);
    globalThis.window = { location: { search: '?view=development' } };
    const dev = renderToStaticMarkup(React.createElement(App));
    assert.match(dev, /Development dashboard/);
    assert.match(dev, /See how it happened/);
    assert.match(dev, /Open main MatchOS page/);
    assert.doesNotMatch(dev, /stadium-hero/);
  } finally {
    globalThis.window = previous;
  }
});

test('Spanish renders the same selected recap and identifies the actual perspective after a failed change', () => {
  const briefing = {
    clock: '75:30',
    audience: 'casual',
    evidence_event_ids: [],
    spoken_recap: { en: 'The score is 2-2.', es: 'El marcador es 2-2.' },
  };
  assert.equal(matchRecap(briefing, 'es'), 'El marcador es 2-2.');
  const html = renderToStaticMarkup(
    React.createElement(FocusedRecap, {
      briefing,
      language: 'es',
      audience: 'advanced',
      error: 'Try again',
    }),
  );
  assert.match(html, /El marcador es 2-2/);
  assert.doesNotMatch(html, /The score is/);
  assert.match(html, /Hasta 75:30.*Aficionado/);
  assert.match(html, /Recap perspective/);
});

test('Spanish evidence describes the same selected change as the displayed paragraph', () => {
  const briefing = {
    clock: '25:00',
    spoken_recap: { es: 'Manchester City registró tres remates durante tu ausencia.' },
    evidence_event_ids: ['e2'],
    story_plan: {
      change_story_id: 'shots:away:1200',
      change_text: { es: 'Entre los minutos 15 y 20, Manchester City registró tres remates.' },
      stories: [{ story_id: 'shots:away:1200', evidence_event_ids: ['e2'] }],
    },
  };
  const html = renderToStaticMarkup(
    React.createElement(FocusedRecap, { briefing, language: 'es', events: [event(2, 'shot')] }),
  );
  assert.match(html, /Qué cambió/);
  assert.match(html, /Entre los minutos 15 y 20, Manchester City/);
  assert.match(html, /Manchester City registró tres remates durante tu ausencia/);
});

test('intentional quiet rule recap is not mislabeled as an Azure outage', () => {
  const briefing = {
    clock: '40:00',
    spoken_recap: { en: 'No qualifying change detected.' },
    narrative: { mode: 'deterministic', fallback_reason: 'no_selected_story' },
    evidence_event_ids: [],
  };
  const html = renderToStaticMarkup(React.createElement(FocusedRecap, { briefing }));
  assert.match(html, /Summary from recorded events · no qualifying change/);
  assert.doesNotMatch(html, /AI writing unavailable/);
});

test('hybrid recap labels its server-calculated metrics', () => {
  const briefing = {
    clock: '25:00',
    spoken_recap: { en: 'Manchester United lead 1-0.' },
    narrative: { mode: 'azure', metric_rendering: 'server_canonical' },
    evidence_event_ids: [],
  };
  const html = renderToStaticMarkup(React.createElement(FocusedRecap, { briefing }));
  assert.match(html, /AI-written recap from recorded match action/);
});

test('player contribution evidence shares the selected bilingual story', () => {
  const briefing = {
    clock: '25:00',
    evidence_event_ids: ['e2'],
    spoken_recap: {
      en: 'Bruno repeatedly found Amad.',
      es: 'Bruno encontró repetidamente a Amad.',
    },
    story_plan: {
      player_story_id: 'player:creator',
      change_story_id: 'player:creator',
      change_text: {
        en: 'Bruno supplied two attempts.',
        es: 'Bruno dio el último pase antes de dos remates.',
      },
      stories: [{ story_id: 'player:creator', evidence_event_ids: ['e2'] }],
    },
  };
  for (const language of ['en', 'es']) {
    const html = renderToStaticMarkup(
      React.createElement(FocusedRecap, { briefing, language, events: [event(2, 'pass')] }),
    );
    assert.match(html, language === 'en' ? /Who shaped the play/ : /Quién influyó en el juego/);
    assert.ok(html.includes(briefing.spoken_recap[language]));
    assert.ok(html.includes(briefing.story_plan.change_text[language]));
  }
});

test('recap replay actions include only playable selected contributions inside the snapshot', () => {
  const pass = event(1, 'pass', {
    player_id: 'h7',
    recipient_player_id: 'h9',
    outcome: 'complete',
    possession_id: 'p1',
    x: 60,
    end_x: 80,
  });
  const shot = event(2, 'shot', { player_id: 'h9', possession_id: 'p1', x: 80, outcome: 'saved' });
  const laterPass = {
    ...pass,
    event_id: 'e3',
    sequence: 3,
    match_second: 4510,
    possession_id: 'p2',
  };
  const laterShot = {
    ...shot,
    event_id: 'e4',
    sequence: 4,
    match_second: 4512,
    possession_id: 'p2',
  };
  const otherShot = { ...laterShot, event_id: 'e5', sequence: 5, player_id: 'h11' };
  const events = [pass, shot, laterPass, laterShot, otherShot];
  const story = {
    story_id: 'selected-player',
    kind: 'player_shot_creation',
    evidence_event_ids: events.map((e) => e.event_id),
    metric: {
      player_id: 'h7',
      links: [
        { pass_event_id: 'e1', shot_event_id: 'e2' },
        { pass_event_id: 'e3', shot_event_id: 'e4' },
        { pass_event_id: 'e3', shot_event_id: 'e5' },
      ],
    },
  };
  const briefing = {
    snapshot: { through_sequence: 2 },
    story_plan: { player_story_id: 'selected-player', stories: [story] },
  };
  assert.deepEqual(
    contributionReplayMoments(briefing, events).map((e) => e.event_id),
    ['e2'],
  );
  briefing.snapshot.through_sequence = 5;
  assert.deepEqual(
    contributionReplayMoments(briefing, events).map((e) => e.event_id),
    ['e2', 'e4'],
  );
  assert.deepEqual(
    contributionReplayMoments(
      { ...briefing, story_plan: { ...briefing.story_plan, player_story_id: 'missing' } },
      events,
    ),
    [],
  );
  assert.deepEqual(contributionReplayMoments(briefing, [shot, laterShot]), []);
});

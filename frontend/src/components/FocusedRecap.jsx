import React from 'react';
import { EvidenceList } from './EvidenceList';
import { matchRecap, contributionReplayMoments, recapReplayLabel } from '../utils/matchFocus';
import { formatMatchSecond } from '../utils/formatters';
import { NarratorControls } from './NarratorControls';

export function FocusedRecap({
  briefing,
  summary,
  events = [],
  busy,
  error,
  onCatchUp,
  audience = 'casual',
  language = 'en',
  onAudienceChange,
  onLanguageChange,
  onListen,
  onReplayMoment,
}) {
  const text = matchRecap(briefing, language);
  const es = language === 'es';
  const shownAudience = briefing?.audience ?? 'casual';
  const upToDate = summary?.evidence_event_ids?.length === 0;
  const sinceLastCheck = !upToDate && briefing?.snapshot?.since_sequence > 0;
  const plan = briefing?.story_plan;
  const replayActions = onReplayMoment ? contributionReplayMoments(briefing, events) : [];
  const primary = plan?.stories?.find((story) => story.story_id === plan.change_story_id);
  const changes = plan
    ? primary
      ? [{ text: plan.change_text?.[language], evidence_event_ids: primary.evidence_event_ids }]
      : []
    : (summary?.explanation?.sections?.filter((section) => section.title === 'What changed') ?? []);
  return (
    <section className="focus-recap" aria-label="Catch Me Up">
      <div className="focus-recap-heading">
        <h2>Catch Me Up</h2>
        <button className="focus-text-button" disabled={busy} onClick={onCatchUp} aria-busy={busy}>
          {busy ? (es ? 'Preparando…' : 'Catching you up…') : es ? 'Ponme al día' : 'Catch me up'}
        </button>
      </div>
      <div className="focus-recap-options">
        <label>
          {es ? 'Enfoque' : 'Perspective'}{' '}
          <select
            aria-label="Recap perspective"
            value={audience}
            disabled={busy}
            onChange={(event) => onAudienceChange?.(event.target.value)}
          >
            <option value="casual">{es ? 'Aficionado' : 'Casual'}</option>
            <option value="advanced">{es ? 'Analista' : 'Analyst'}</option>
          </select>
        </label>
        <label>
          {es ? 'Idioma' : 'Language'}{' '}
          <select
            aria-label="Recap language"
            value={language}
            onChange={(event) => onLanguageChange?.(event.target.value)}
          >
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
        </label>
      </div>
      <p className="focus-caption">
        {sinceLastCheck
          ? es
            ? 'Desde tu última consulta, con el contexto del partido.'
            : 'Since your last catch-up — with the match context.'
          : es
            ? 'La historia, los cambios y la situación actual.'
            : 'The story, the changes, and what matters now.'}
      </p>
      {upToDate && (
        <p className="focus-caught-up" role="status">
          {es
            ? 'Estás al día. No hay nuevas acciones registradas desde tu última consulta.'
            : 'You’re caught up. No new recorded action since your last check.'}
        </p>
      )}
      <p className="focus-recap-prose">
        {text || 'Catch Me Up connects the moments you missed as match events arrive.'}
      </p>
      {replayActions.length > 0 && (
        <div
          className="recap-action-replays"
          aria-label={es ? 'Jugadas de este resumen' : 'Actions behind this recap'}
        >
          <span>{es ? 'Mira las jugadas del resumen' : 'See the actions behind the recap'}</span>
          {replayActions.slice(0, 3).map((event) => (
            <button key={event.event_id} onClick={() => onReplayMoment(event)}>
              {recapReplayLabel(event, briefing, language)} ·{' '}
              {formatMatchSecond(event.match_second)}
            </button>
          ))}
        </div>
      )}
      {briefing && (
        <NarratorControls story={briefing} language={language} compact onListen={onListen} />
      )}
      {briefing && (
        <span className="focus-caption">
          {es ? 'Hasta' : 'As of'} {briefing.clock} ·{' '}
          {shownAudience === 'advanced'
            ? es
              ? 'Analista'
              : 'Analyst'
            : es
              ? 'Aficionado'
              : 'Casual'}{' '}
          ·{' '}
          {briefing.narrative?.mode === 'azure'
            ? es
              ? 'Resumen con IA a partir de las acciones registradas'
              : 'AI-written recap from recorded match action'
            : briefing.narrative?.fallback_reason === 'limited_coverage'
              ? es
                ? 'Resumen de acciones registradas · cobertura limitada'
                : 'Summary from recorded events · limited coverage'
              : briefing.narrative?.fallback_reason === 'no_selected_story'
                ? es
                  ? 'Resumen de acciones registradas · sin cambios relevantes'
                  : 'Summary from recorded events · no qualifying change'
                : es
                  ? 'Resumen de acciones registradas · sin redacción con IA'
                  : 'Summary from recorded events · AI writing unavailable'}
        </span>
      )}
      {error && (
        <p className="focus-error" role="alert">
          {error}{' '}
          <button className="focus-text-button" onClick={onCatchUp} disabled={busy}>
            {es ? 'Reintentar' : 'Retry'}
          </button>
        </p>
      )}
      {briefing && (
        <details className="focus-evidence">
          <summary>{es ? 'Consultar acciones registradas' : 'Inspect supporting events'}</summary>
          <p className="focus-caption">
            {es
              ? `Acciones que respaldan el resumen hasta ${briefing.clock}.`
              : `Actions supporting the recap up to ${briefing.clock}.`}
          </p>
          {(es && !plan ? [] : changes).map((section, index) => (
            <div className="focus-analysis" key={index}>
              <h3>
                {plan?.player_story_id
                  ? es
                    ? 'Quién influyó en el juego'
                    : 'Who shaped the play'
                  : es
                    ? 'Qué cambió'
                    : 'What changed'}
              </h3>
              <p>{section.text}</p>
              <EvidenceList
                evidenceIds={section.evidence_event_ids ?? []}
                events={events}
                language={language}
              />
            </div>
          ))}
          <h3 className="focus-analysis-title">
            {es ? 'Evidencias del resumen' : 'Recap evidence'}
          </h3>
          <EvidenceList
            evidenceIds={briefing.evidence_event_ids ?? []}
            events={events}
            language={language}
          />
        </details>
      )}
    </section>
  );
}

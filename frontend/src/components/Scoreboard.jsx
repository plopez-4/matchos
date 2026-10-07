import React, { useEffect, useRef, useState } from 'react';
import { formatMatchSecond } from '../utils/formatters';
import { teams, newScoringTeams } from '../utils/teams';

export function Scoreboard({ analytics, events = [] }) {
  const homeGoals = analytics?.teams?.home?.goal ?? 0;
  const awayGoals = analytics?.teams?.away?.goal ?? 0;
  const previousScore = useRef(null);
  const serial = useRef(0);
  const [celebrations, setCelebrations] = useState([]);
  const goal = celebrations[0];
  useEffect(() => {
    if (!analytics) return;
    const current = { home: homeGoals, away: awayGoals };
    const previous = previousScore.current;
    if (previous && (current.home < previous.home || current.away < previous.away)) {
      setCelebrations([]);
    } else {
      const scored = newScoringTeams(previous, current);
      if (scored.length)
        setCelebrations((queue) => [
          ...queue,
          ...scored.map((team) => ({
            team,
            key: ++serial.current,
            score: `${homeGoals} – ${awayGoals}`,
          })),
        ]);
    }
    previousScore.current = current;
  }, [analytics, homeGoals, awayGoals]);
  useEffect(() => {
    if (!goal) return;
    const timer = setTimeout(() => setCelebrations((queue) => queue.slice(1)), 6000);
    return () => clearTimeout(timer);
  }, [goal?.key]);

  const homeShots = analytics?.teams?.home?.shot ?? 0;
  const awayShots = analytics?.teams?.away?.shot ?? 0;

  const homePasses = analytics?.teams?.home?.pass ?? 0;
  const awayPasses = analytics?.teams?.away?.pass ?? 0;

  const homeRecoveries = analytics?.teams?.home?.recovery ?? 0;
  const awayRecoveries = analytics?.teams?.away?.recovery ?? 0;

  const latestEvent = events.length > 0 ? events[events.length - 1] : null;
  const recordedSecond = latestEvent?.match_second ?? 0;
  const recordedPeriod = latestEvent?.period ?? 1;
  const formattedClock = formatMatchSecond(recordedSecond);

  return (
    <section className="dashboard-card scoreboard-card" aria-label="Match Scoreboard">
      <div className="fixture-label">
        <span>THE MATCH CENTRE</span>
        <span>FICTIONAL FIXTURE · SYNTHETIC REPLAY</span>
      </div>
      <div className="goal-announcement" role="status" aria-live="polite" aria-atomic="true">
        {goal ? `${teams[goal.team].name} goal. Score ${goal.score}.` : ''}
      </div>
      {goal && (
        <div
          key={goal.key}
          className={`goal-takeover goal-${goal.team}`}
          aria-hidden="true"
          style={{ '--goal-color': teams[goal.team].color, '--goal-ink': teams[goal.team].ink }}
        >
          <div className="goal-stripes" />
          <span className="goal-team">{teams[goal.team].name}</span>
          <strong className="goal-word">GOAL</strong>
          <span className="goal-score">{goal.score}</span>
          <span className="goal-caption">THE MOMENT THAT CHANGES THE MATCH.</span>
        </div>
      )}
      <div className="scoreboard-main">
        <div className="team-cell team-home">
          <div className="team-avatar home-avatar">HFC</div>
          <div className="team-info">
            <h2 className="team-name">Home FC</h2>
            <span className="team-role">
              <span className="kit-dot kit-home" /> White kit · Attacking Right →
            </span>
          </div>
        </div>

        <div className="score-center">
          <div className="score-display">
            <span className="score-number score-home">{homeGoals}</span>
            <span className="score-divider">–</span>
            <span className="score-number score-away">{awayGoals}</span>
          </div>
          <div className="match-clock-wrap">
            <span className="clock-badge">
              <span className="clock-icon">⏱</span>
              <span className="clock-time">{formattedClock}</span>
              <span className="clock-period">P{recordedPeriod}</span>
            </span>
          </div>
          <span className="clock-disclaimer">
            Recorded match time · static when simulator pauses
          </span>
        </div>

        <div className="team-cell team-away">
          <div className="team-info text-right">
            <h2 className="team-name">Away FC</h2>
            <span className="team-role">
              <span className="kit-dot kit-away" /> Red kit · ← Attacking Left
            </span>
          </div>
          <div className="team-avatar away-avatar">AFC</div>
        </div>
      </div>

      <div className="stats-strip" aria-label="Recorded highlights metrics">
        <div className="stat-item">
          <span className="stat-label">Highlights</span>
          <span className="stat-value">{events.length}</span>
          <span className="stat-sub">recorded</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Recorded Shots</span>
          <span className="stat-value">
            <strong className="stat-home">{homeShots}</strong>
            <span className="stat-sep">:</span>
            <strong className="stat-away">{awayShots}</strong>
          </span>
          <span className="stat-sub">H vs A</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Recorded Passes</span>
          <span className="stat-value">
            <strong className="stat-home">{homePasses}</strong>
            <span className="stat-sep">:</span>
            <strong className="stat-away">{awayPasses}</strong>
          </span>
          <span className="stat-sub">H vs A</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Recoveries</span>
          <span className="stat-value">
            <strong className="stat-home">{homeRecoveries}</strong>
            <span className="stat-sep">:</span>
            <strong className="stat-away">{awayRecoveries}</strong>
          </span>
          <span className="stat-sub">H vs A</span>
        </div>
      </div>
    </section>
  );
}

import React, { useState, useEffect } from 'react';
import { resolveScenario } from './utils/scenarios';
import { Matchday } from './components/Matchday';
import { FanMatch } from './components/FanMatch';
import './matchday.css';
import './focus.css';
import './fan.css';

export function App() {
  const [experience, setExperience] = useState(() =>
    ['development', 'matchday'].includes(new URLSearchParams(window.location.search).get('view'))
      ? 'matchday'
      : 'single',
  );
  const [matchId, setMatchId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('match');
    return requested && /^[a-zA-Z0-9_-]{1,80}$/.test(requested)
      ? requested
      : `replay-${crypto.randomUUID()}`;
  });
  const [scenarioId, setScenarioId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('scenario');
    return resolveScenario(requested);
  });
  const [autoStart, setAutoStart] = useState(false);

  useEffect(() => {
    if (experience !== 'single') return;
    const url = new URL(window.location.href);
    url.searchParams.set('match', matchId);
    window.history.replaceState(null, '', url);
  }, [matchId, experience]);

  const newMatch = (play, targetScenario = scenarioId) => {
    const id = `replay-${crypto.randomUUID()}`;
    const url = new URL(window.location.href);
    url.searchParams.set('match', id);
    url.searchParams.set('scenario', targetScenario);
    window.history.replaceState(null, '', url);
    setAutoStart(play);
    setScenarioId(targetScenario);
    setMatchId(id);
  };

  const handleScenarioChange = (newScenario) => {
    const target = resolveScenario(newScenario);
    newMatch(false, target);
  };

  const chooseExperience = (next) => {
    const url = new URL(window.location.href);
    if (next === 'matchday') url.searchParams.set('view', 'development');
    else url.searchParams.delete('view');
    window.history.replaceState(null, '', url);
    setExperience(next);
  };

  return (
    <>
      {experience === 'matchday' && (
        <nav className="experience-nav" aria-label="Development dashboard">
          <button onClick={() => chooseExperience('single')}>← Open main MatchOS page</button>
        </nav>
      )}
      {experience === 'matchday' ? (
        <Matchday />
      ) : (
        <FanMatch
          key={`${matchId}:${scenarioId}`}
          matchId={matchId}
          scenarioId={scenarioId}
          autoStart={autoStart}
          onNewMatch={newMatch}
          onScenarioChange={handleScenarioChange}
        />
      )}
    </>
  );
}

import React, { useState } from 'react';
import { resolveScenario } from './utils/scenarios';
import { Matchday } from './components/Matchday';
import { FanMatchday } from './components/FanMatchday';
import './matchday.css';
import './focus.css';
import './fan.css';

export function App() {
  const [experience, setExperience] = useState(() =>
    ['development', 'matchday'].includes(new URLSearchParams(window.location.search).get('view'))
      ? 'matchday'
      : 'single',
  );
  const [scenarioId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('scenario');
    return resolveScenario(requested);
  });

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
      {experience === 'matchday' ? <Matchday /> : <FanMatchday initialScenarioId={scenarioId} />}
    </>
  );
}

import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import variants from '../../backend/app/data/match_variants.json' with { type: 'json' };
import fixtures from '../../backend/app/data/demo_fixtures.json' with { type: 'json' };
import { replayId } from './utils/replayId';
import { releaseMatchday } from './api';
import './testing.css';

const clock = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
function TestingHub() {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const restore = () => setBusy(false);
    window.addEventListener('pageshow', restore);
    return () => window.removeEventListener('pageshow', restore);
  }, []);
  async function open(fixture, version) {
    setBusy(true);
    setError('');
    try {
      const previous = sessionStorage.getItem('matchos-fixed-test-day');
      if (previous) {
        try {
          await releaseMatchday(previous);
        } catch (err) {
          if (![401, 403, 404].includes(err.status)) throw err;
        }
      }
      const day = replayId(`test-v${version}`);
      sessionStorage.setItem('matchos-fixed-test-day', day);
      const query = new URLSearchParams({ day, scenario: fixture.id });
      window.location.assign(`/?${query}`);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }
  return (
    <main>
      <a href="/">← MatchOS</a>
      <h1>Fixed test matches</h1>
      <p>
        Choose the exact version. Each button starts a fresh replay with the selected version for
        all three fixtures. Switching matches keeps that version and the shared clock.
      </p>
      <p>
        <strong>Pause before returning here.</strong> Reopening a case clears your previous test
        replay in this tab. These are fictional recorded events, not predictions.
      </p>
      <details>
        <summary>What to test on each case</summary>
        <ol>
          <li>
            Start on Normal. Switch to Fast to reach a checkpoint, then pause. A goal at :11 appears
            at the next 30-second clock step.
          </li>
          <li>
            Catch Me Up: check score, scorer/time, team pass ownership and chronology against
            supporting events. Record the actual AI-written or fallback label.
          </li>
          <li>
            Change English/Spanish and Casual/Analyst. Listen with both available voices. Check
            names, consecutive team names and times.
          </li>
          <li>
            Follow a goal build-up, pause/resume and return to the match. Switch fixtures and
            confirm the shared clock stays consistent.
          </li>
          <li>
            For red-card cases, stay on a different fixture around 35:00, 55:00 or 60:00. Check the
            alert, correct fixture/event, no duplicate dispatch, expiry and no later action by the
            dismissed player.
          </li>
          <li>
            On Android: check text at normal zoom, all buttons fit, 44px touch controls, no
            horizontal scrolling, recap readability, audio and portrait/landscape.
          </li>
        </ol>
        <p>
          Do not request every AI variation repeatedly: the demo has bounded Azure capacity. Record
          failures instead of rerunning until an answer passes.
        </p>
      </details>
      {error && <p role="alert">{error}</p>}
      {fixtures.map((fixture) => (
        <section key={fixture.role}>
          <h2>{fixture.name}</h2>
          <div className="test-grid">
            {variants[fixture.role].map((config, index) => (
              <article key={index}>
                <h3>
                  Version {index + 1} · {config.name}
                </h3>
                <p>
                  Goals:{' '}
                  {config.goals.length
                    ? config.goals
                        .map(
                          (second) =>
                            `${fixture[config.shots[String(second)]]} · ${clock(second + 11)}`,
                        )
                        .join('; ')
                    : 'None — confirm the recap does not invent one.'}
                </p>
                {config.red_card && (
                  <p>
                    Sending-off: {fixture[config.red_card.team]} · {clock(config.red_card.second)}.
                    Check immediately before and after.
                  </p>
                )}
                {config.post_match_red_card && (
                  <p>
                    After full time: a player on losing {fixture[config.post_match_red_card.team]}{' '}
                    is dismissed for abusive language towards the referee. Check the explanation,
                    final score and unchanged playing numbers.
                  </p>
                )}
                <p>
                  Pause at:{' '}
                  {config.red_card
                    ? `${clock(config.red_card.second - 30)}, ${clock(config.red_card.second + 30)}, `
                    : ''}
                  25:00, half-time, 75:30 and full-time. Check only events already reached.
                </p>
                <button disabled={busy} onClick={() => open(fixture, index + 1)}>
                  Open version {index + 1}
                </button>
              </article>
            ))}
          </div>
        </section>
      ))}
      <p>
        Use this page on the same origin as MatchOS. On a phone, replace the computer's localhost
        address with its private network address. Do not share a localhost link with remote testers.
      </p>
    </main>
  );
}
createRoot(document.getElementById('root')).render(<TestingHub />);

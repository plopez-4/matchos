import React from 'react';

export function SimulatorGuide({ matchId = 'demo-match' }) {
  const replayCommand =
    '.\\.venv\\Scripts\\python.exe simulator/run.py --seed 7 --count 30 --interval 0.5 --api http://127.0.0.1:8000' +
    (matchId === 'demo-match' ? '' : ` --match-id ${matchId}`);

  const copyCommand = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(replayCommand);
    }
  };

  return (
    <section className="dashboard-card guide-card" aria-label="Simulator Instructions">
      <div className="card-header">
        <div className="header-text-group">
          <div className="title-with-pill">
            <h2 className="card-title">Simulator Replay Idle</h2>
            <span className="feature-pill badge-activity">Ready for Events</span>
          </div>
          <p className="card-subtitle">
            No events are currently loaded in the backend in-memory store. Run the simulator to feed
            the demo scenario.
          </p>
        </div>
      </div>

      <div className="guide-body">
        <p>Open a terminal in the project root and run the synthetic scenario replay:</p>

        <div className="command-box">
          <code>{replayCommand}</code>
          <button
            type="button"
            className="btn-copy"
            onClick={copyCommand}
            title="Copy command to clipboard"
          >
            Copy
          </button>
        </div>

        <div className="guide-expectations">
          <h4>What this scenario provides:</h4>
          <ul>
            <li>
              <strong>30 synthetic events</strong> spanning 10:00 of match time.
            </li>
            <li>
              <strong>Score:</strong> Home FC 1–0 Away FC (goal at 9:31).
            </li>
            <li>
              <strong>Activity shift:</strong> Home recorded 4 shots in minutes 5–10 vs 1 in minutes
              0–5.
            </li>
            <li>
              <strong>Grounded stories:</strong> Goal story & shot activity comparison story.
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}

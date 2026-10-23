import React from 'react';

export function CompetitionBranding() {
  return (
    <div className="competition-strip">
      <div className="league-identity">
        <img src="/assets/premier-league.svg" alt="Premier League" width="126" height="54" />
        <span>
          INSIDE THE GAME
          <br />
          <strong>DEVELOPER HACKATHON</strong>
        </span>
      </div>
      <div className="microsoft-credit">
        <span className="microsoft-mark" aria-hidden="true">
          <i />
          <i />
          <i />
          <i />
        </span>
        <span>
          Built with
          <br />
          <strong>Microsoft Azure</strong>
        </span>
      </div>
    </div>
  );
}

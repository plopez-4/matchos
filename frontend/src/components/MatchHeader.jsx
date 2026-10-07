import React from 'react';

export function MatchHeader({ status = 'connected', error = '', lastUpdated = null }) {
  const getStatusBadge = () => {
    switch (status) {
      case 'connected':
        return (
          <span className="status-pill status-connected" title="Active HTTP polling every 2 seconds">
            <span className="status-dot"></span>
            Connected · Replay
          </span>
        );
      case 'stale':
        return (
          <span className="status-pill status-stale" title="Backend unreachable; showing last snapshot">
            <span className="status-dot"></span>
            Reconnecting · Cached
          </span>
        );
      case 'empty':
        return (
          <span className="status-pill status-empty" title="Backend active but no replay events loaded yet">
            <span className="status-dot"></span>
            Simulator Idle
          </span>
        );
      case 'loading':
      default:
        return (
          <span className="status-pill status-loading">
            <span className="status-dot"></span>
            Connecting…
          </span>
        );
    }
  };

  return (
    <header className="match-header">
      <div className="competition-strip">
        <div className="league-identity"><img src="/assets/premier-league.svg" alt="Premier League" width="126" height="54" /><span>INSIDE THE GAME<br /><strong>DEVELOPER HACKATHON</strong></span></div>
        <div className="microsoft-credit"><span className="microsoft-mark" aria-hidden="true"><i /><i /><i /><i /></span><span>Powered by<br /><strong>Microsoft Azure</strong></span></div>
      </div>
      <div className="stadium-hero">
        <img className="stadium-photo" src="/assets/goodison-park.webp" alt="Aerial photograph of Goodison Park football stadium in Liverpool" />
        <div className="hero-editorial"><p>BEYOND THE SCORELINE.</p><h2>Every match<br /><em>has a story.</em></h2><span>Find the moments. Understand the changes.</span></div>
        <span className="hero-location">GOODISON PARK · LIVERPOOL</span>
      </div>
      <p className="photo-credit">Photo: <a href="https://www.arne-mueseler.com" target="_blank" rel="noreferrer">Arne Müseler / arne-mueseler.com</a> · <a href="https://creativecommons.org/licenses/by-sa/3.0/de/deed.en" target="_blank" rel="noreferrer">CC BY-SA 3.0 DE</a> · Display cropped with a purple overlay.</p>
      <div className="header-top-row">
        <div className="brand-group">
          <p className="eyebrow">THE AI OPERATING SYSTEM FOR LIVE FOOTBALL</p>
          <div className="brand-title-wrap">
            <h1 className="brand-title">MatchOS</h1>
            <span className="synthetic-badge" title="Fictional synthetic replay for Microsoft/Premier League Hackathon">
              Synthetic Replay
            </span>
          </div>
          <p className="product-summary">
            Deterministic event analytics, connected match stories, and personalized Azure AI catch-up briefings for live football.
          </p>
        </div>

        <div className="header-meta">
          <div className="meta-pills">
            {getStatusBadge()}
          </div>
          {lastUpdated && (
            <span className="last-sync-time">
              Last synced: {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="connection-alert" role="alert">
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}
    </header>
  );
}

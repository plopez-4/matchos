import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

async function api(path, options) {
  const response = await fetch('/api' + path, options);
  if (!response.ok) throw new Error('API request failed (' + response.status + ')');
  return response.json();
}
function App() {
  const [data, setData] = useState({ events: [], stories: [], analytics: null });
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);
  const [audience, setAudience] = useState('casual');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    let timer;
    async function refresh() {
      try {
        const [events, stories, analytics] = await Promise.all(['events', 'stories', 'analytics'].map(name => api('/matches/demo-match/' + name)));
        if (active) { setData({ events, stories, analytics }); setError(''); }
      } catch (e) { if (active) setError(e.message + '. Check that the backend is running.'); }
      finally { if (active) timer = setTimeout(refresh, 2000); }
    }
    refresh();
    return () => { active = false; clearTimeout(timer); };
  }, []);
  async function catchUp() {
    setBusy(true);
    try {
      setSummary(await api('/matches/demo-match/catch-up', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ since_sequence: summary?.through_sequence ?? 0, audience }) }));
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <main>
    <header><p className="eyebrow">THE AI OPERATING SYSTEM FOR LIVE FOOTBALL</p><h1>MatchOS</h1><p>Home FC vs Away FC · Synthetic demo</p></header>
    {error && <p role="alert">{error}</p>}
    <section><h2>Match pulse</h2><p className="score">{data.analytics?.teams.home.goal ?? 0} — {data.analytics?.teams.away.goal ?? 0}</p><p>{data.events.length} recorded events · Refreshes every 2 seconds</p></section>
    <section><h2>Catch Me Up</h2><label>Explanation style <select value={audience} onChange={e => setAudience(e.target.value)}><option value="casual">Casual</option><option value="advanced">Advanced</option></select></label> <button onClick={catchUp} disabled={busy}>{busy ? 'Loading…' : 'Catch Me Up'}</button>
    <p>{summary?.summary ?? 'Get a summary of the events you missed.'}</p>{summary && <details><summary>Supporting event IDs</summary><p>{summary.evidence_event_ids.join(', ') || 'No new events.'}</p></details>}</section>
    <section><h2>Match stories</h2>{data.stories.length === 0 && <p>Goal stories appear during replay. Run the simulator to begin.</p>}{data.stories.map(story => <article key={story.story_id}><p>{story.text}</p><small>Evidence: {story.evidence_event_ids.join(', ')} · {story.rule_version}</small></article>)}</section>
    <section><h2>Recent events</h2><ol>{data.events.slice(-10).reverse().map(e => <li key={e.event_id}>{Math.floor(e.match_second / 60)}:{String(e.match_second % 60).padStart(2, '0')} · {e.team_id} · {e.type} <small>({e.event_id})</small></li>)}</ol></section>
    <footer>Deterministic demo explanations. Tactical AI and full story graph planned.</footer>
  </main>;
}
createRoot(document.getElementById('root')).render(<App />);

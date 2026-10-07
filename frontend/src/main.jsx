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
        if (active) {
          setData({ events, stories, analytics }); setError('');
          setSummary(old => old && old.through_sequence > (events.at(-1)?.sequence ?? 0) ? null : old);
        }
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
    <section><h2>Match pulse</h2><p className="score">{data.analytics?.teams.home.goal ?? 0} — {data.analytics?.teams.away.goal ?? 0}</p><p>{data.events.length} recorded highlights · Refreshes every 2 seconds</p><p>Shots: Home {data.analytics?.teams.home.shot ?? 0} · Away {data.analytics?.teams.away.shot ?? 0}</p></section>
    <section><h2>Attacking activity</h2>{!data.analytics?.shot_windows?.length && <p>Waiting for two complete five-minute windows.</p>}{data.analytics?.shot_windows?.map(w => <p key={w.team_id}>{w.team_id === 'home' ? 'Home' : 'Away'}: {w.current.shot_count} shots in minutes {w.current.start_second / 60}–{w.current.end_second / 60} · {w.previous.shot_count} in the previous five minutes.</p>)}<small>Recorded shots describe shooting activity; they do not measure possession or tactical pressure.</small></section>
    <section><h2>Catch Me Up</h2><label>Explanation style <select value={audience} onChange={e => setAudience(e.target.value)}><option value="casual">Casual</option><option value="advanced">Advanced</option></select></label> <button onClick={catchUp} disabled={busy}>{busy ? 'Loading…' : 'Catch Me Up'}</button>
    <p>{summary?.summary ?? 'Get a summary of the events you missed.'}</p>{summary?.explanation && <p><small>{summary.explanation.mode === 'azure' ? 'Stories selected by Azure AI · facts checked against match evidence' : 'Rule-based summary'}</small></p>}{summary && <details><summary>Supporting event IDs</summary><p>New events: {summary.evidence_event_ids.join(', ') || 'No new events.'}</p><p>Story context (may include earlier events): {summary.context_evidence_event_ids?.join(', ') || 'None.'}</p></details>}{summary?.explanation?.trace?.length > 0 && <details><summary>How stories were selected</summary><ul>{summary.explanation.trace.map((step, index) => <li key={index}>{step.step === 'get_match_evidence' ? 'Retrieved verified match stories' : step.step === 'verify_selection' ? 'Checked selected stories against available evidence' : 'Used the rule-based fallback'} · {step.status}</li>)}</ul></details>}</section>
    <section><h2>Match stories</h2>{data.stories.length === 0 && <p>Run the scenario to see a goal story and a five-minute activity comparison.</p>}{data.stories.map(story => <article key={story.story_id}><p>{story.text}</p><small>{story.rule_version}</small><details><summary>Inspect supporting events ({story.evidence_event_ids.length})</summary><ul>{story.evidence_event_ids.map(id => {
      const event = data.events.find(e => e.event_id === id);
      return <li key={id}>{event ? Math.floor(event.match_second / 60) + ':' + String(event.match_second % 60).padStart(2, '0') + ' · ' + event.team_id + ' · ' + event.type + (event.outcome ? ' · ' + event.outcome : '') : 'Event not loaded'} <small>{id}</small></li>;
    })}</ul></details></article>)}</section>
    <section><h2>Recent events</h2><ol>{data.events.slice(-10).reverse().map(e => <li key={e.event_id}>{Math.floor(e.match_second / 60)}:{String(e.match_second % 60).padStart(2, '0')} · {e.team_id} · {e.type} <small>({e.event_id})</small></li>)}</ol></section>
    <footer>Fictional highlights with evidence-linked stories. Azure AI story selection is optional; displayed facts come from verified match rules.</footer>
  </main>;
}
createRoot(document.getElementById('root')).render(<App />);

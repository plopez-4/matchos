let sessionReady;

async function ensureSession() {
  if (!sessionReady) {
    sessionReady = fetch('/api/session', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-MatchOS-Client': 'replay' },
      body: '{}',
    })
      .then((response) => {
        if (!response.ok) throw new Error('Could not establish replay session. Please reload.');
      })
      .catch((error) => {
        sessionReady = undefined;
        throw error;
      });
  }
  return sessionReady;
}

async function request(path, options = {}) {
  if (options.method === 'POST' || options.method === 'DELETE') await ensureSession();
  const url = '/api' + path;
  const response = await fetch(url, {
    ...options,
    credentials: 'same-origin',
    headers: { ...options.headers, 'X-MatchOS-Client': 'replay' },
  });
  if (response.status === 401) sessionReady = undefined;
  if (!response.ok) {
    let errorDetail = '';
    try {
      const errJson = await response.json();
      errorDetail = errJson?.detail || errJson?.message || '';
    } catch {
      // Non-JSON error body
    }
    const message = errorDetail
      ? `API error (${response.status}): ${errorDetail}`
      : `API request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export async function fetchHealth() {
  return request('/health');
}

export function fetchReplayScenarios(options = {}) {
  return request('/replay/scenarios', options);
}

export function fetchReplayScenario(matchId, scenarioId = 'legacy-default', options = {}) {
  let scId = scenarioId;
  let opt = options;
  if (typeof scenarioId === 'object' && scenarioId !== null) {
    opt = scenarioId;
    scId = 'legacy-default';
  }
  return request('/replay/start', {
    ...opt,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ match_id: matchId, scenario_id: scId }),
  });
}

export function ingestReplayEvent(event, options = {}) {
  return request(`/matches/${encodeURIComponent(event.match_id)}/advance`, {
    ...options,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sequence: event.sequence }),
  });
}

export async function fetchMatchData(matchId = 'demo-match', options = {}) {
  const [events, stories, analytics] = await Promise.all([
    request(`/matches/${matchId}/events`, options),
    request(`/matches/${matchId}/stories`, options),
    request(`/matches/${matchId}/analytics`, options),
  ]);
  return { events, stories, analytics };
}

export async function fetchMatchGraph(matchId = 'demo-match', options = {}) {
  return request(`/matches/${matchId}/graph`, options);
}

export async function postCatchUp(
  matchId = 'demo-match',
  { since_sequence = 0, audience = 'casual' },
  options = {},
) {
  return request(`/matches/${matchId}/catch-up`, {
    ...options,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ since_sequence, audience }),
  });
}

export function startMatchday(matchdayId, options = {}) {
  return request('/matchdays/start', {
    ...options,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ matchday_id: matchdayId }),
  });
}

export function fetchMatchday(id, options = {}) {
  return request(`/matchdays/${encodeURIComponent(id)}`, options);
}

export function tickMatchday(id, tick, options = {}) {
  return request(`/matchdays/${encodeURIComponent(id)}/tick`, {
    ...options,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tick }),
  });
}

export function releaseMatchday(id, options = {}) {
  return request(`/matchdays/${encodeURIComponent(id)}`, {
    ...options,
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
}

let sessionReady;
let narrationStatus;

export function fetchNarrationStatus({ refresh = false } = {}) {
  if (refresh) narrationStatus = undefined;
  if (!narrationStatus)
    narrationStatus = request('/narration/status').catch(() => ({
      available: false,
      profiles: [],
    }));
  return narrationStatus;
}

async function narrationAudio(path, payload, { signal } = {}) {
  await ensureSession();
  const deadline = AbortSignal.timeout(20000);
  const response = await fetch('/api' + path, {
    method: 'POST',
    credentials: 'same-origin',
    signal: signal ? AbortSignal.any([signal, deadline]) : deadline,
    headers: { 'Content-Type': 'application/json', 'X-MatchOS-Client': 'replay' },
    body: JSON.stringify(payload),
  });
  if (response.status === 401) sessionReady = undefined;
  if (!response.ok) {
    let message = 'Narration could not be generated';
    try {
      message = (await response.json()).detail || message;
    } catch {}
    throw new Error(message);
  }
  if (!response.headers.get('content-type')?.startsWith('audio/mpeg'))
    throw new Error('Narration returned no playable audio');
  return { blob: await response.blob(), clock: response.headers.get('X-MatchOS-Snapshot') };
}

export function fetchNarration(snapshot, language, voice_profile, options = {}) {
  return narrationAudio(
    '/narration',
    {
      ...snapshot,
      language,
      voice_profile,
      audience: options.audience ?? 'casual',
      ...(options.selectedStoryIds ? { selected_story_ids: options.selectedStoryIds } : {}),
      ...(options.narrativeId ? { narrative_id: options.narrativeId } : {}),
    },
    options,
  );
}
export function auditionNarrator(language, voice_profile, options = {}) {
  return narrationAudio('/narration/audition', { language, voice_profile }, options);
}

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

export function fetchReplayScenario(matchId, scenarioId = 'united-city-90', options = {}) {
  let scId = scenarioId;
  let opt = options;
  if (typeof scenarioId === 'object' && scenarioId !== null) {
    opt = scenarioId;
    scId = 'united-city-90';
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
    body: JSON.stringify({ matchday_id: matchdayId, resume_on_capacity: true }),
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

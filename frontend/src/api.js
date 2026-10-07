async function request(path, options = {}) {
  const url = '/api' + path;
  const response = await fetch(url, options);
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

export async function postCatchUp(matchId = 'demo-match', { since_sequence = 0, audience = 'casual' }, options = {}) {
  return request(`/matches/${matchId}/catch-up`, {
    ...options,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ since_sequence, audience }),
  });
}

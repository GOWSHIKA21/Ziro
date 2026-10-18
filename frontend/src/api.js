const rawBase = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = rawBase ? `${rawBase.replace(/\/$/, '')}/api` : '/api';

export async function fetchLearningPaths() {
  const res = await fetch(`${API_BASE}/learning-paths`);
  if (!res.ok) throw new Error('Failed to load learning paths');
  return res.json();
}

export async function getLearningPath(id) {
  const res = await fetch(`${API_BASE}/learning-paths/${id}`);
  if (!res.ok) throw new Error(`Failed to load learning path: ${id}`);
  return res.json();
}

export async function createLearningPath(data) {
  const res = await fetch(`${API_BASE}/learning-paths`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create learning path');
  }
  return res.json();
}

export async function generateLearningPlan(id, options = {}) {
  const params = new URLSearchParams();
  if (options.simulate_paid) params.append('simulate_paid', options.simulate_paid);
  if (options.simulate_broken) params.append('simulate_broken', options.simulate_broken);
  
  const url = `${API_BASE}/learning-paths/${id}/generate${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to generate learning plan');
  return res.json();
}

export async function verifyResources(id, options = {}) {
  const params = new URLSearchParams();
  if (options.simulate_paid_resource_id) params.append('simulate_paid_resource_id', options.simulate_paid_resource_id);
  if (options.simulate_broken_resource_id) params.append('simulate_broken_resource_id', options.simulate_broken_resource_id);

  const url = `${API_BASE}/learning-paths/${id}/verify${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to verify resources');
  return res.json();
}

export async function replaceResource(pathId, resourceId, reason) {
  const res = await fetch(`${API_BASE}/learning-paths/${pathId}/replace-resource/${resourceId}?reason=${encodeURIComponent(reason || 'User requested replacement')}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to replace resource');
  return res.json();
}

export async function approveAction(actionId, notes = '') {
  const res = await fetch(`${API_BASE}/actions/${actionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision: 'approve', notes })
  });
  if (!res.ok) throw new Error('Failed to approve action');
  return res.json();
}

export async function rejectAction(actionId, notes = '') {
  const res = await fetch(`${API_BASE}/actions/${actionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision: 'reject', notes })
  });
  if (!res.ok) throw new Error('Failed to reject action');
  return res.json();
}

export async function editAction(actionId, payload) {
  const res = await fetch(`${API_BASE}/actions/${actionId}/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to edit action');
  }
  return res.json();
}

export async function toggleSessionComplete(sessionId) {
  const res = await fetch(`${API_BASE}/calendar/sessions/${sessionId}/toggle-complete`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to toggle session completion');
  return res.json();
}

export function getCalendarIcsDownloadUrl(pathId) {
  return `${API_BASE}/calendar/export-ics?learning_request_id=${pathId}`;
}

export function getRoadmapMarkdownDownloadUrl(pathId) {
  return `${API_BASE}/learning-paths/${pathId}/export-markdown`;
}


export async function syncCalendar(pathId) {
  const res = await fetch(`${API_BASE}/learning-paths/${pathId}/sync-calendar`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to sync calendar');
  return res.json();
}

export async function fetchCalendarSessions(pathId = null) {
  const url = pathId ? `${API_BASE}/calendar/sessions?learning_request_id=${pathId}` : `${API_BASE}/calendar/sessions`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch calendar sessions');
  return res.json();
}

export async function createCustomSession(payload) {
  const res = await fetch(`${API_BASE}/calendar/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to create custom session');
  return res.json();
}

export async function deleteCalendarSession(sessionId) {
  const res = await fetch(`${API_BASE}/calendar/sessions/${sessionId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete session');
  return res.json();
}

export async function executeTestRuns(scenarioId = 'ALL') {
  const res = await fetch(`${API_BASE}/test-runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_id: scenarioId })
  });
  if (!res.ok) throw new Error('Failed to execute test runs');
  return res.json();
}

export async function fetchTestRuns() {
  const res = await fetch(`${API_BASE}/test-runs`);
  if (!res.ok) throw new Error('Failed to fetch test runs');
  return res.json();
}

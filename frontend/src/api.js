const rawBase = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = rawBase ? `${rawBase.replace(/\/$/, '')}/api` : '/api';

const TOKEN_KEY = 'ziro_auth_token';
const GUEST_SESSION_KEY = 'ziro_guest_session_id';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function generateCryptographicallySecureToken() {
  try {
    if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues) {
      const bytes = new Uint8Array(24); // 192 bits of entropy
      window.crypto.getRandomValues(bytes);
      return 'gst_' + Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch {}
  try {
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      const bytes = new Uint8Array(24);
      crypto.getRandomValues(bytes);
      return 'gst_' + Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch {}
  return 'gst_' + Date.now().toString(36) + Math.random().toString(36).substring(2, 15);
}

export function getGuestSessionId() {
  try {
    let guestId = sessionStorage.getItem(GUEST_SESSION_KEY);
    if (!guestId) {
      guestId = generateCryptographicallySecureToken();
      sessionStorage.setItem(GUEST_SESSION_KEY, guestId);
    }
    return guestId;
  } catch {
    return 'gst_ephemeral_' + Math.random().toString(36).substring(2, 15);
  }
}

export function clearGuestSessionId() {
  try {
    sessionStorage.removeItem(GUEST_SESSION_KEY);
  } catch {}
}

function getAuthHeaders(customHeaders = {}) {
  const token = getAuthToken();
  const guestId = !token ? getGuestSessionId() : null;
  return {
    ...customHeaders,
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(guestId ? { 'X-Guest-Session-ID': guestId } : {})
  };
}

// ----------------- Authentication -----------------

export async function registerUser(payload) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Registration failed');
  }
  const data = await res.json();
  if (data.access_token) setAuthToken(data.access_token);
  return data;
}

export async function loginUser(payload) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Invalid email or password');
  }
  const data = await res.json();
  if (data.access_token) setAuthToken(data.access_token);
  return data;
}

export async function getMe() {
  const token = getAuthToken();
  if (!token) return null;
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    clearAuthToken();
    return null;
  }
  return res.json();
}

export async function logoutUser() {
  clearAuthToken();
  clearGuestSessionId();
  await fetch(`${API_BASE}/auth/logout`, { method: 'POST' }).catch(() => {});
  return true;
}

export async function getGoogleOAuthConfig() {
  try {
    const res = await fetch(`${API_BASE}/auth/google/config`);
    if (!res.ok) return { client_id: '', is_configured: false };
    return await res.json();
  } catch {
    return { client_id: '', is_configured: false };
  }
}

export async function loginWithGoogle(credential) {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential })
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Google authentication failed');
  }
  const data = await res.json();
  if (data.access_token) setAuthToken(data.access_token);
  return data;
}

// ----------------- Learning Paths -----------------

export async function fetchLearningPaths() {
  const res = await fetch(`${API_BASE}/learning-paths`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to load learning paths');
  return res.json();
}

export async function getLearningPath(id) {
  const res = await fetch(`${API_BASE}/learning-paths/${id}`, {
    headers: getAuthHeaders()
  });
  if (res.status === 401) {
    throw new Error('Authentication required to access this learning path.');
  }
  if (res.status === 403) {
    throw new Error('Access denied: You do not have permission to view this learning path.');
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || `Failed to load learning path: ${id}`);
  }
  return res.json();
}

export async function createLearningPath(data) {
  const res = await fetch(`${API_BASE}/learning-paths`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create learning path');
  }
  return res.json();
}

export async function deleteLearningPath(id) {
  const res = await fetch(`${API_BASE}/learning-paths/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (res.status === 401) {
    throw new Error('Authentication required to delete this learning path.');
  }
  if (res.status === 403) {
    throw new Error('Access denied: You do not have permission to delete this learning path.');
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to delete learning path');
  }
  return res.json();
}

export async function generateLearningPlan(id, options = {}) {
  const params = new URLSearchParams();
  if (options.simulate_paid) params.append('simulate_paid', options.simulate_paid);
  if (options.simulate_broken) params.append('simulate_broken', options.simulate_broken);
  
  const url = `${API_BASE}/learning-paths/${id}/generate${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to generate learning plan');
  return res.json();
}

export async function adaptLearningPlan(pathId, payload) {
  const res = await fetch(`${API_BASE}/learning-paths/${pathId}/adapt`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to adapt learning plan');
  }
  return res.json();
}

export async function verifyResources(id, options = {}) {
  const params = new URLSearchParams();
  if (options.simulate_paid_resource_id) params.append('simulate_paid_resource_id', options.simulate_paid_resource_id);
  if (options.simulate_broken_resource_id) params.append('simulate_broken_resource_id', options.simulate_broken_resource_id);

  const url = `${API_BASE}/learning-paths/${id}/verify${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to verify resources');
  return res.json();
}

export async function replaceResource(pathId, resourceId, reason) {
  const res = await fetch(`${API_BASE}/learning-paths/${pathId}/replace-resource/${resourceId}?reason=${encodeURIComponent(reason || 'User requested replacement')}`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to replace resource');
  return res.json();
}

// ----------------- Actions & Approval -----------------

export async function approveAction(actionId, notes = '') {
  const res = await fetch(`${API_BASE}/actions/${actionId}/approve`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ decision: 'approve', notes })
  });
  if (!res.ok) throw new Error('Failed to approve action');
  return res.json();
}

export async function rejectAction(actionId, notes = '') {
  const res = await fetch(`${API_BASE}/actions/${actionId}/reject`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ decision: 'reject', notes })
  });
  if (!res.ok) throw new Error('Failed to reject action');
  return res.json();
}

export async function editAction(actionId, payload) {
  const res = await fetch(`${API_BASE}/actions/${actionId}/edit`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to edit action');
  }
  return res.json();
}

// ----------------- Calendar & Progress -----------------

export async function toggleSessionComplete(sessionId, payload = null) {
  const res = await fetch(`${API_BASE}/calendar/sessions/${sessionId}/toggle-complete`, {
    method: 'POST',
    headers: getAuthHeaders(payload ? { 'Content-Type': 'application/json' } : {}),
    body: payload ? JSON.stringify(payload) : undefined
  });
  if (!res.ok) throw new Error('Failed to toggle session completion');
  return res.json();
}

export async function downloadCalendarIcs(pathId) {
  const res = await fetch(`${API_BASE}/calendar/export-ics?learning_request_id=${pathId}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to download iCalendar schedule');
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `study_schedule_${pathId}.ics`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function downloadRoadmapMarkdown(pathId) {
  const res = await fetch(`${API_BASE}/learning-paths/${pathId}/export-markdown`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to download roadmap Markdown');
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `roadmap_${pathId}.md`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function getCalendarIcsDownloadUrl(pathId) {
  return `${API_BASE}/calendar/export-ics?learning_request_id=${pathId}`;
}

export function getRoadmapMarkdownDownloadUrl(pathId) {
  return `${API_BASE}/learning-paths/${pathId}/export-markdown`;
}

export async function syncCalendar(pathId) {
  const res = await fetch(`${API_BASE}/learning-paths/${pathId}/sync-calendar`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to sync calendar');
  return res.json();
}

export async function createCustomSession(payload) {
  const res = await fetch(`${API_BASE}/calendar/sessions`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to create custom session');
  return res.json();
}

export async function deleteCalendarSession(sessionId) {
  const res = await fetch(`${API_BASE}/calendar/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete session');
  return res.json();
}

// ----------------- Google Calendar OAuth -----------------

export async function getCalendarOAuthStatus() {
  try {
    const res = await fetch(`${API_BASE}/calendar/oauth/status`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return { is_connected: false, client_id_configured: false };
    return await res.json();
  } catch {
    return { is_connected: false, client_id_configured: false };
  }
}

export async function getCalendarAuthorizeUrl(redirectTo) {
  const query = redirectTo ? `?redirect_to=${encodeURIComponent(redirectTo)}` : '';
  const res = await fetch(`${API_BASE}/calendar/oauth/authorize${query}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to generate calendar authorization URL');
  }
  return await res.json();
}

export async function disconnectGoogleCalendar() {
  const res = await fetch(`${API_BASE}/calendar/oauth/disconnect`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to disconnect Google Calendar');
  }
  return await res.json();
}


// ----------------- Official Test Runs -----------------

export async function executeTestRuns(scenarioId = 'ALL') {
  const res = await fetch(`${API_BASE}/test-runs`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ scenario_id: scenarioId })
  });
  if (!res.ok) throw new Error('Failed to execute test runs');
  return res.json();
}

export async function fetchTestRuns() {
  const res = await fetch(`${API_BASE}/test-runs`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch test runs');
  return res.json();
}

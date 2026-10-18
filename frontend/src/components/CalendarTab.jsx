import React, { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon, Clock, Plus, RefreshCw, CheckCircle2,
  ShieldCheck, AlertCircle, Trash2, User, Sparkles, Download, ExternalLink,
  Check, LogOut, Link2
} from 'lucide-react';
import {
  downloadCalendarIcs,
  getCalendarOAuthStatus,
  getCalendarAuthorizeUrl,
  disconnectGoogleCalendar,
  getAuthToken
} from '../api';

export default function CalendarTab({
  learningPath,
  currentUser,
  onOpenAuthModal,
  onSyncCalendar,
  onCreateCustomSession,
  onDeleteSession,
  onToggleComplete,
  isSyncing
}) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [customTitle, setCustomTitle] = useState('My Custom Cohort Review');
  const [customDate, setCustomDate] = useState(new Date().toISOString().split('T')[0]);
  const [customStartTime, setCustomStartTime] = useState('19:00');
  const [customEndTime, setCustomEndTime] = useState('21:00');
  const [syncFeedback, setSyncFeedback] = useState(null);

  // Google Calendar OAuth state
  const [oauthStatus, setOauthStatus] = useState({ is_connected: false, calendar_email: null, client_id_configured: false });
  const [isOauthLoading, setIsOauthLoading] = useState(false);
  const [oauthMessage, setOauthMessage] = useState(null);

  // Fetch calendar connection status and handle OAuth callback query params
  useEffect(() => {
    let isMounted = true;

    async function loadStatus() {
      try {
        const st = await getCalendarOAuthStatus();
        if (isMounted) setOauthStatus(st);
      } catch (err) {
        console.warn('Failed to fetch calendar OAuth status', err);
      }
    }
    loadStatus();

    // Check query params for OAuth result
    const params = new URLSearchParams(window.location.search);
    if (params.get('calendar_connected') === 'true') {
      setOauthMessage({
        type: 'success',
        text: 'Google Calendar connected successfully! Your study sessions can now sync live to your Google Calendar.'
      });
      params.delete('calendar_connected');
      const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : '');
      window.history.replaceState({}, '', newUrl);
      loadStatus();
    } else if (params.get('calendar_error')) {
      setOauthMessage({
        type: 'error',
        text: `Google Calendar connection error: ${decodeURIComponent(params.get('calendar_error'))}`
      });
      params.delete('calendar_error');
      const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : '');
      window.history.replaceState({}, '', newUrl);
    }

    return () => {
      isMounted = false;
    };
  }, [currentUser]);

  const handleConnectGoogleCalendar = async () => {
    if (!getAuthToken() && !currentUser) {
      if (onOpenAuthModal) onOpenAuthModal();
      return;
    }
    setIsOauthLoading(true);
    setOauthMessage(null);
    try {
      const res = await getCalendarAuthorizeUrl(window.location.href);
      if (res.auth_url) {
        window.location.href = res.auth_url;
      }
    } catch (err) {
      setOauthMessage({
        type: 'error',
        text: err.message || 'Failed to initiate Google Calendar connection.'
      });
      setIsOauthLoading(false);
    }
  };

  const handleDisconnectGoogleCalendar = async () => {
    setIsOauthLoading(true);
    setOauthMessage(null);
    try {
      await disconnectGoogleCalendar();
      setOauthStatus(prev => ({ ...prev, is_connected: false, calendar_email: null }));
      setOauthMessage({
        type: 'info',
        text: 'Google Calendar disconnected. The system will use the persistent mock calendar and RFC 5545 export.'
      });
    } catch (err) {
      setOauthMessage({
        type: 'error',
        text: err.message || 'Failed to disconnect Google Calendar.'
      });
    } finally {
      setIsOauthLoading(false);
    }
  };


  if (!learningPath) {
    return (
      <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 p-8 shadow-xs">
        <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
          <CalendarIcon className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">No Learning Path Selected</h3>
        <p className="text-slate-500 text-sm max-w-md mx-auto mt-1">
          Select or create a learning path to schedule study sessions, sync with Google Calendar, or export RFC 5545 .ics files.
        </p>
      </div>
    );
  }
  const { study_sessions = [], id: pathId, weekly_hours } = learningPath;

  const completedCount = study_sessions.filter(s => s.status === 'completed').length;
  const progressPercent = study_sessions.length > 0 ? Math.round((completedCount / study_sessions.length) * 100) : 0;

  const handleSync = async () => {
    try {
      const res = await onSyncCalendar(pathId);
      setSyncFeedback(res);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateCustom = async (e) => {
    e.preventDefault();
    await onCreateCustomSession({
      learning_request_id: pathId,
      title: customTitle,
      scheduled_date: customDate,
      start_time: customStartTime,
      end_time: customEndTime,
      duration_hours: 2.0
    });
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Calendar Controls */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Idempotent Calendar Engine
            </span>
            <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
              Preserves User-Created Events
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Study Session Calendar & Schedule
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Synchronizes approved study blocks into calendar events without duplicating existing sessions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Universal iCal export */}
          {study_sessions.length > 0 && (
            <button
              onClick={() => downloadCalendarIcs(pathId)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors shadow-2xs"
              title="Download standard RFC 5545 iCalendar file for Google Calendar, Apple Calendar, or Outlook"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export iCal (.ics)</span>
            </button>
          )}

          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Custom Session</span>
          </button>

          <button
            onClick={handleSync}
            disabled={isSyncing}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>Sync Approved Sessions</span>
          </button>
        </div>
      </div>

      {/* Google Calendar OAuth Connection Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs transition-all">
        {oauthMessage && (
          <div className={`mb-4 p-3.5 rounded-xl border text-xs flex items-center justify-between gap-2 animate-in fade-in ${
            oauthMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : oauthMessage.type === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : 'bg-blue-50 border-blue-200 text-blue-800'
          }`}>
            <div className="flex items-center gap-2">
              {oauthMessage.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{oauthMessage.text}</span>
            </div>
            <button
              onClick={() => setOauthMessage(null)}
              className="text-slate-400 hover:text-slate-600 font-bold px-1"
            >
              ×
            </button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center shrink-0 shadow-2xs">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-bold text-sm text-slate-900">Google Calendar OAuth 2.0</span>
                {oauthStatus.is_connected ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Connected ({oauthStatus.calendar_email || 'Primary Calendar'})
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                    Mock / Disconnected
                  </span>
                )}
                <span className="text-[10px] font-medium text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded-md border border-slate-200">
                  Scope: calendar.events
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {oauthStatus.is_connected
                  ? 'Your study blocks sync directly to your personal Google Calendar with automatic reminder notifications.'
                  : 'Connect your personal Google Calendar to sync study blocks live, or continue using the local mock calendar with RFC 5545 .ics export.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
            {oauthStatus.is_connected ? (
              <button
                type="button"
                onClick={handleDisconnectGoogleCalendar}
                disabled={isOauthLoading}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl transition-colors disabled:opacity-50"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>{isOauthLoading ? 'Disconnecting...' : 'Disconnect Calendar'}</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleConnectGoogleCalendar}
                disabled={isOauthLoading}
                className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-800 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl shadow-2xs transition-colors disabled:opacity-50"
              >
                {isOauthLoading ? (
                  <span className="w-3.5 h-3.5 border-2 border-slate-700 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Link2 className="w-3.5 h-3.5 text-blue-600" />
                )}
                <span>Connect Google Calendar</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress Bar when sessions exist */}

      {study_sessions.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <span className="font-bold text-slate-800">Study Session Progress:</span>
            <span className="text-slate-500">{completedCount} of {study_sessions.length} completed ({progressPercent}%)</span>
          </div>
          <div className="w-full sm:w-64 bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Sync Feedback Alert */}
      {syncFeedback && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 flex items-start justify-between gap-3 text-xs text-blue-900 animate-in fade-in">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
            <div>
              <span className="font-bold">Sync Completed ({syncFeedback.integration_mode}): </span>
              <span>
                Added {syncFeedback.added_missing_sessions} missing sessions. Prevented {syncFeedback.skipped_duplicates} duplicate blocks. Preserved {syncFeedback.preserved_user_events} user events. Total calendar events: {syncFeedback.total_calendar_events}.
              </span>
            </div>
          </div>
          <button
            onClick={() => setSyncFeedback(null)}
            className="text-blue-500 hover:text-blue-800 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Sessions Grid */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CalendarIcon className="w-4 h-4 text-slate-700" />
            <h3 className="font-bold text-sm text-slate-900">
              Scheduled Calendar Events ({study_sessions.length} sessions)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Target: {weekly_hours}h / week</span>
        </div>

        {study_sessions.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500">
            <CalendarIcon className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p>No calendar study sessions currently synced.</p>
            <p className="mt-1">
              Go to the <span className="font-semibold text-blue-600">Approval Center</span> to approve proposed calendar study blocks, or click "Sync Approved Sessions".
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {study_sessions.map((sess) => {
              const isDone = sess.status === 'completed';

              return (
                <div
                  key={sess.id}
                  className={`p-4 rounded-xl border transition-all ${
                    isDone
                      ? 'bg-emerald-50/30 border-emerald-300'
                      : sess.is_user_created
                      ? 'bg-amber-50/40 border-amber-200'
                      : 'bg-slate-50/50 border-slate-200 hover:border-blue-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold text-slate-500 bg-white border border-slate-200 px-2 py-0.5 rounded">
                        Week {sess.week_number}
                      </span>
                      {sess.is_user_created ? (
                        <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded flex items-center gap-1">
                          <User className="w-2.5 h-2.5" /> User Created (Preserved)
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                          Agent Synced
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      {/* Mark Completed Toggle */}
                      {onToggleComplete && (
                        <button
                          onClick={() => onToggleComplete(sess.id)}
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition-colors ${
                            isDone
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                          title="Toggle study session completion"
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          <span>{isDone ? 'Completed' : 'Mark Done'}</span>
                        </button>
                      )}

                      {sess.is_user_created && (
                        <button
                          onClick={() => onDeleteSession(sess.id)}
                          className="text-slate-400 hover:text-rose-600 transition-colors p-1"
                          title="Delete session"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <h4 className={`font-bold text-sm mb-1 ${isDone ? 'line-through text-slate-500' : 'text-slate-900'}`}>
                    {sess.title}
                  </h4>

                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-2">
                    <div className="flex items-center gap-1">
                      <CalendarIcon className="w-3.5 h-3.5 text-slate-400" />
                      <span>{sess.scheduled_date}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{sess.start_time} - {sess.end_time}</span>
                    </div>
                  </div>

                  <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] text-slate-400">
                    <span className="text-emerald-700 font-semibold">{sess.duration_hours}h block</span>
                    
                    {/* One-Click Google Calendar link */}
                    {sess.google_calendar_url && (
                      <a
                        href={sess.google_calendar_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline font-medium inline-flex items-center gap-0.5"
                        title="Add to Google Calendar in one click"
                      >
                        <span>+ Google Cal</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Custom Session Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in">
            <h3 className="font-bold text-slate-900 text-base mb-1">Add Custom Study Session</h3>
            <p className="text-xs text-slate-500 mb-4">
              Create a custom user event to test that calendar synchronization strictly preserves user sessions.
            </p>

            <form onSubmit={handleCreateCustom} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                  Event Title
                </label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                  Scheduled Date
                </label>
                <input
                  type="date"
                  value={customDate}
                  onChange={(e) => setCustomDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={customStartTime}
                    onChange={(e) => setCustomStartTime(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                    End Time
                  </label>
                  <input
                    type="time"
                    value={customEndTime}
                    onChange={(e) => setCustomEndTime(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>

              <div className="pt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
                >
                  Save User Session
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

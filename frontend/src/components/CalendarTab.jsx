import React, { useState } from 'react';
import {
  Calendar as CalendarIcon, Clock, Plus, RefreshCw, CheckCircle2,
  ShieldCheck, AlertCircle, Trash2, User, Sparkles, Download, ExternalLink
} from 'lucide-react';
import { getCalendarIcsDownloadUrl } from '../api';

export default function CalendarTab({
  learningPath,
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

  if (!learningPath) return null;
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
            <a
              href={getCalendarIcsDownloadUrl(pathId)}
              download={`study_schedule_${pathId}.ics`}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors shadow-2xs"
              title="Download standard RFC 5545 iCalendar file for Google Calendar, Apple Calendar, or Outlook"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export iCal (.ics)</span>
            </a>
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

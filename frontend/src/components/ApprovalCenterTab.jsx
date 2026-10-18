import React, { useState } from 'react';
import {
  ShieldAlert, Check, X, Calendar, BookOpen, ExternalLink,
  ShieldCheck, AlertCircle, Clock, CheckCircle2, Hash, Edit3
} from 'lucide-react';

export default function ApprovalCenterTab({
  learningPath,
  onApproveAction,
  onRejectAction,
  onEditAction
}) {
  const [processingId, setProcessingId] = useState(null);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [actionTypeFilter, setActionTypeFilter] = useState('all');
  
  // Edit Action State
  const [editingAction, setEditingAction] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editTime, setEditTime] = useState('');
  const [editDuration, setEditDuration] = useState(2.5);

  if (!learningPath) return null;
  const { proposed_actions = [] } = learningPath;

  const filteredActions = proposed_actions.filter(a => {
    if (actionTypeFilter === 'enrollment') return a.action_type === 'course_enrollment';
    if (actionTypeFilter === 'calendar') return a.action_type === 'calendar_block';
    if (actionTypeFilter === 'pending') return a.approval_status === 'Pending Approval';
    return true;
  });

  const handleApprove = async (actionId) => {
    setProcessingId(actionId);
    try {
      await onApproveAction(actionId, decisionNotes || 'Approved by user via Approval Center');
      setDecisionNotes('');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (actionId) => {
    setProcessingId(actionId);
    try {
      await onRejectAction(actionId, decisionNotes || 'Rejected by user via Approval Center');
      setDecisionNotes('');
    } finally {
      setProcessingId(null);
    }
  };

  const openEditModal = (action) => {
    setEditingAction(action);
    setEditTitle(action.title);
    setEditTime(action.schedule_details?.suggested_time || '18:30 - 21:00');
    setEditDuration(action.schedule_details?.duration_per_session_hours || 2.5);
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    if (!editingAction || !onEditAction) return;
    setProcessingId(editingAction.id);
    try {
      const payload = {
        title: editTitle,
        schedule_details: {
          ...editingAction.schedule_details,
          suggested_time: editTime,
          duration_per_session_hours: parseFloat(editDuration)
        }
      };
      await onEditAction(editingAction.id, payload);
      setEditingAction(null);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md flex items-center gap-1 border border-amber-200">
              <ShieldAlert className="w-3.5 h-3.5" /> Human-in-the-Loop Gate
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Proposed Action Approval Center
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Explicit authorization required. Review, customize (Edit), and Approve or Reject course enrollments & calendar blocks.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {[
            { id: 'all', label: `All Actions (${proposed_actions.length})` },
            { id: 'pending', label: `Pending (${proposed_actions.filter(a => a.approval_status === 'Pending Approval').length})` },
            { id: 'enrollment', label: 'Enrollments' },
            { id: 'calendar', label: 'Calendar Blocks' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActionTypeFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                actionTypeFilter === tab.id
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Action Cards List */}
      <div className="space-y-4">
        {filteredActions.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-xs text-slate-500">
            No proposed actions matching current filter.
          </div>
        ) : (
          filteredActions.map((action) => {
            const isPending = action.approval_status === 'Pending Approval';
            const isApproved = action.approval_status === 'Approved';
            const isRejected = action.approval_status === 'Rejected';
            const isEnrollment = action.action_type === 'course_enrollment';
            const isProcessing = processingId === action.id;

            return (
              <div
                key={action.id}
                className={`bg-white rounded-2xl border p-5 shadow-xs transition-all ${
                  isPending
                    ? 'border-amber-300 ring-1 ring-amber-100'
                    : isApproved
                    ? 'border-emerald-200 bg-emerald-50/20'
                    : 'border-slate-200 opacity-70'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-slate-100">
                  <div className="flex items-start gap-3.5">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                      isEnrollment ? 'bg-blue-100 text-blue-700' : 'bg-indigo-100 text-indigo-700'
                    }`}>
                      {isEnrollment ? <BookOpen className="w-5 h-5" /> : <Calendar className="w-5 h-5" />}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                          {isEnrollment ? 'Course Enrollment' : 'Calendar Study Block'}
                        </span>
                        
                        {/* Approval Status Badge */}
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                          isPending
                            ? 'bg-amber-100 text-amber-800'
                            : isApproved
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {action.approval_status}
                        </span>

                        {/* Execution Status Badge */}
                        <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-slate-400" />
                          Exec: {action.execution_status}
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-slate-900 mt-1">
                        {action.title}
                      </h3>
                      <p className="text-xs text-slate-600 mt-0.5">{action.description}</p>
                    </div>
                  </div>

                  {/* Explicit Decision Controls: Edit, Reject, Approve */}
                  <div className="flex items-center gap-2 shrink-0 self-end lg:self-center">
                    {isPending ? (
                      <>
                        <button
                          onClick={() => openEditModal(action)}
                          disabled={isProcessing}
                          className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors flex items-center gap-1.5 disabled:opacity-50"
                          title="Edit action schedule parameters before approving"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>

                        <button
                          onClick={() => handleReject(action.id)}
                          disabled={isProcessing}
                          className="px-3.5 py-1.5 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl transition-colors flex items-center gap-1.5 disabled:opacity-50"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>

                        <button
                          onClick={() => handleApprove(action.id)}
                          disabled={isProcessing}
                          className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
                        >
                          {isProcessing ? (
                            <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5" />
                          )}
                          <span>Approve & Execute</span>
                        </button>
                      </>
                    ) : (
                      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1 rounded-lg">
                        Decision Recorded ({action.approval_status})
                      </span>
                    )}
                  </div>
                </div>

                {/* Details Grid */}
                <div className="pt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-600">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="font-semibold text-slate-500 uppercase text-[10px] block">Target Destination</span>
                    {isEnrollment ? (
                      <a
                        href={action.destination}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline font-medium inline-flex items-center gap-1 mt-0.5 break-all"
                      >
                        <span>Verified Portal Link</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="font-medium text-slate-800">{action.destination}</span>
                    )}
                  </div>

                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="font-semibold text-slate-500 uppercase text-[10px] block">Schedule / Account</span>
                    <span className="text-slate-800 font-medium">
                      {isEnrollment 
                        ? (action.requires_permissions || 'No account required')
                        : `${action.schedule_details?.suggested_time || '18:30 - 21:00'} (${action.schedule_details?.duration_per_session_hours || 2.5}h)`
                      }
                    </span>
                  </div>

                  <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="font-semibold text-slate-500 uppercase text-[10px] block flex items-center gap-1">
                      <Hash className="w-3 h-3 text-slate-400" /> Idempotency Protection
                    </span>
                    <span className="font-mono text-[10px] text-slate-700 block truncate" title={action.idempotency_key}>
                      {action.idempotency_key}
                    </span>
                  </div>
                </div>

                {/* Execution Result Details */}
                {action.execution_result && (
                  <div className="mt-3 p-2.5 rounded-lg bg-emerald-50/60 border border-emerald-200/60 text-xs text-emerald-900 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>{action.execution_result.status || action.execution_result.instructions || 'Action executed and verified.'}</span>
                    </div>
                    {action.executed_at && (
                      <span className="text-[10px] text-emerald-700 shrink-0 font-mono">
                        {new Date(action.executed_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Edit Action Modal */}
      {editingAction && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-slate-900 text-base">Edit Proposed Action</h3>
              <button
                onClick={() => setEditingAction(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Modify the proposed schedule or title before granting human approval.
            </p>

            <form onSubmit={saveEdit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                  Action Title
                </label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {editingAction.action_type === 'calendar_block' && (
                <>
                  <div>
                    <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                      Suggested Time Slot
                    </label>
                    <input
                      type="text"
                      value={editTime}
                      onChange={(e) => setEditTime(e.target.value)}
                      placeholder="e.g. 19:00 - 21:30"
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[10px] mb-1">
                      Duration per Session (Hours)
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="1"
                      max="8"
                      value={editDuration}
                      onChange={(e) => setEditDuration(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </>
              )}

              <div className="pt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingAction(null)}
                  className="px-3 py-1.5 font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={processingId === editingAction.id}
                  className="px-4 py-1.5 font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
                >
                  Save Modifications
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

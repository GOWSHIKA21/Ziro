import React, { useState } from 'react';
import { X, RefreshCw, Zap, CheckCircle2, Clock, AlertTriangle, ArrowRight } from 'lucide-react';
import { adaptLearningPlan } from '../api';

export default function AdaptiveRecoveryModal({ isOpen, onClose, learningPath, onAdaptSuccess }) {
  const [newWeeklyHours, setNewWeeklyHours] = useState(learningPath?.weekly_hours || 5.0);
  const [strategy, setStrategy] = useState('rebalance');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen || !learningPath) return null;

  const completedSessions = learningPath.study_sessions?.filter(
    (s) => s.status === 'completed' || (s.actual_minutes_studied && s.actual_minutes_studied > 0)
  ) || [];

  const completedHours = completedSessions.reduce((acc, s) => acc + (s.duration_hours || 0), 0);
  const remainingHours = Math.max(0, (learningPath.total_available_hours || 130) - completedHours);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const updated = await adaptLearningPlan(learningPath.id, {
        new_weekly_hours: parseFloat(newWeeklyHours),
        missed_strategy: strategy
      });
      onAdaptSuccess(updated);
      onClose();
    } catch (err) {
      setError(err.message || 'Adaptive replanning failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-amber-500 flex items-center justify-center text-white shadow-md shadow-amber-500/20">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Adaptive Recovery Planner</h2>
            <p className="text-xs text-slate-500">
              Rebalance study load, adjust for missed sessions, or update weekly availability.
            </p>
          </div>
        </div>

        {/* Current State Summary Card */}
        <div className="mb-6 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 grid grid-cols-3 gap-3 text-center">
          <div className="p-2">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Completed</p>
            <p className="text-lg font-extrabold text-emerald-600">{completedHours.toFixed(1)}h</p>
            <p className="text-[10px] text-slate-500">{completedSessions.length} sessions</p>
          </div>
          <div className="p-2 border-x border-slate-200">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Remaining</p>
            <p className="text-lg font-extrabold text-blue-600">{remainingHours.toFixed(1)}h</p>
            <p className="text-[10px] text-slate-500">pending load</p>
          </div>
          <div className="p-2">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Current Rate</p>
            <p className="text-lg font-extrabold text-slate-800">{learningPath.weekly_hours}h/wk</p>
            <p className="text-[10px] text-slate-500">{learningPath.duration_weeks} wks total</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              New Weekly Availability (Hours per Week)
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                step="0.5"
                min="1"
                max="40"
                required
                value={newWeeklyHours}
                onChange={(e) => setNewWeeklyHours(e.target.value)}
                className="w-32 px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm font-bold text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
              <span className="text-xs text-slate-500">
                At {newWeeklyHours}h/wk, remaining {remainingHours.toFixed(1)}h takes ~{Math.ceil(remainingHours / (parseFloat(newWeeklyHours) || 1))} weeks.
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Recovery Strategy
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => setStrategy('rebalance')}
                className={`p-3 rounded-xl border text-left text-xs transition-all ${
                  strategy === 'rebalance'
                    ? 'border-amber-500 bg-amber-50/50 text-slate-900 font-semibold ring-1 ring-amber-500'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <p className="font-bold text-slate-900 mb-0.5">Rebalance</p>
                <p className="text-[11px] text-slate-500">
                  Redistribute remaining topics without repeating completed work.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setStrategy('extend')}
                className={`p-3 rounded-xl border text-left text-xs transition-all ${
                  strategy === 'extend'
                    ? 'border-amber-500 bg-amber-50/50 text-slate-900 font-semibold ring-1 ring-amber-500'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <p className="font-bold text-slate-900 mb-0.5">Extend Timeline</p>
                <p className="text-[11px] text-slate-500">
                  Lower weekly pressure and smoothly extend the completion date.
                </p>
              </button>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold shadow-md shadow-amber-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  <span>Apply Adaptive Replanning</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

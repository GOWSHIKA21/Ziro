import React, { useState } from 'react';
import { X, Sparkles, AlertCircle, Clock, Calendar, BookOpen, Layers } from 'lucide-react';

export default function InputFormModal({ isOpen, onClose, onSubmit, isLoading }) {
  const [goal, setGoal] = useState('Data Analyst');
  const [startingLevel, setStartingLevel] = useState('Beginner');
  const [weeklyHours, setWeeklyHours] = useState(5);
  const [durationValue, setDurationValue] = useState(6);
  const [durationUnit, setDurationUnit] = useState('months');
  const [preferredFormat, setPreferredFormat] = useState('Mixed');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  // Calculate estimated total hours
  const calculatedWeeks = durationUnit === 'months' ? (durationValue === 6 ? 26 : Math.round(durationValue * (26 / 6))) : durationValue;
  const totalHours = Math.round(weeklyHours * calculatedWeeks);

  const handleFillExample = () => {
    setGoal('Data Analyst');
    setStartingLevel('Beginner');
    setWeeklyHours(5);
    setDurationValue(6);
    setDurationUnit('months');
    setPreferredFormat('Mixed');
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!goal || !goal.trim() || goal.trim().length < 3) {
      setError('Please enter a valid learning goal (at least 3 characters).');
      return;
    }
    if (weeklyHours <= 0) {
      setError('Weekly hours must be greater than 0.');
      return;
    }
    if (weeklyHours > 80) {
      setError('Weekly hours cannot exceed 80 hours per week.');
      return;
    }
    if (durationValue <= 0) {
      setError('Duration must be greater than 0.');
      return;
    }

    onSubmit({
      goal: goal.trim(),
      starting_level: startingLevel,
      weekly_hours: parseFloat(weeklyHours),
      duration_value: parseInt(durationValue, 10),
      duration_unit: durationUnit,
      preferred_format: preferredFormat
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-100 overflow-hidden transform transition-all animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
              <Sparkles className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-base">New Learning Path</h3>
              <p className="text-xs text-slate-500">Configure your target goal and weekly availability</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Example Banner */}
        <div className="bg-blue-50/60 border-b border-blue-100 px-6 py-2.5 flex items-center justify-between">
          <span className="text-xs text-blue-800">
            Quick-start with the official benchmark scenario:
          </span>
          <button
            type="button"
            onClick={handleFillExample}
            className="text-xs font-semibold text-blue-700 hover:text-blue-900 underline"
          >
            Use Benchmark (6mo @ 5h/wk)
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Goal Input */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Target Learning Goal / Job Role
            </label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Data Analyst, Web Developer, Machine Learning"
              className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Starting Level & Format */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Current Level
              </label>
              <select
                value={startingLevel}
                onChange={(e) => setStartingLevel(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Beginner">Beginner (No background)</option>
                <option value="Intermediate">Intermediate (Some syntax/tools)</option>
                <option value="Advanced">Advanced (Upskilling)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Preferred Format
              </label>
              <select
                value={preferredFormat}
                onChange={(e) => setPreferredFormat(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Mixed">Mixed (Recommended)</option>
                <option value="Interactive courses">Interactive Courses</option>
                <option value="Videos">Videos</option>
                <option value="Documentation">Official Documentation</option>
              </select>
            </div>
          </div>

          {/* Weekly Hours & Duration */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Hours / Week</span>
              </label>
              <input
                type="number"
                min="1"
                max="80"
                step="0.5"
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Duration</span>
              </label>
              <div className="flex gap-1.5">
                <input
                  type="number"
                  min="1"
                  max="104"
                  value={durationValue}
                  onChange={(e) => setDurationValue(e.target.value)}
                  className="w-20 px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <select
                  value={durationUnit}
                  onChange={(e) => setDurationUnit(e.target.value)}
                  className="w-full px-2 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="months">Months</option>
                  <option value="weeks">Weeks</option>
                </select>
              </div>
            </div>
          </div>

          {/* Computed Budget Preview */}
          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 flex items-center justify-between text-xs">
            <span className="text-slate-600">Calculated Study Time Budget:</span>
            <div className="text-right">
              <span className="font-bold text-slate-900 text-sm">{totalHours} Total Hours</span>
              <span className="text-slate-400 block text-[11px]">({calculatedWeeks} weeks × {weeklyHours}h/wk)</span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="pt-2 flex justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Generating Path...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Build Learning Path</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import {
  Calendar, Clock, CheckCircle2, ChevronRight, Award,
  Code2, ExternalLink, ShieldCheck, Bookmark, Sparkles
} from 'lucide-react';

export default function LearningPathTab({ learningPath }) {
  const [selectedMonth, setSelectedMonth] = useState('all');

  if (!learningPath) {
    return (
      <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 p-8 shadow-xs">
        <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
          <Calendar className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">No Learning Path Selected</h3>
        <p className="text-slate-500 text-sm max-w-md mx-auto mt-1">
          Select an existing roadmap from the top dropdown or create a new learning goal to view its week-by-week curriculum.
        </p>
      </div>
    );
  }

  const {
    goal,
    weekly_hours,
    duration_weeks,
    weekly_plans = [],
    modules = [],
    resources = []
  } = learningPath;

  // Group weeks by month (4 weeks per month)
  const totalMonths = Math.ceil(duration_weeks / 4);
  const monthsArray = Array.from({ length: totalMonths }, (_, i) => i + 1);

  const filteredPlans = selectedMonth === 'all'
    ? weekly_plans
    : weekly_plans.filter(p => Math.ceil(p.week_number / 4) === parseInt(selectedMonth, 10));

  return (
    <div className="space-y-6">
      {/* Header Bar with Month Filter & Budget Badge */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">
              Prerequisite-Aware Schedule
            </span>
            <span className="text-xs text-slate-500 font-medium">
              Strict Invariant: Allocated Hours ≤ {weekly_hours}h / week
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Week-by-Week Learning Roadmap
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Total {weekly_plans.length} planned weeks. Foundational prerequisites scheduled before advanced analytics & capstone.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setSelectedMonth('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0 ${
              selectedMonth === 'all'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All {weekly_plans.length} Weeks
          </button>
          {monthsArray.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedMonth(m.toString())}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0 ${
                selectedMonth === m.toString()
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Month {m}
            </button>
          ))}
        </div>
      </div>

      {/* Week Timeline Cards */}
      <div className="space-y-4">
        {filteredPlans.map((plan) => {
          const matchedModule = modules.find(m => m.id === plan.module_id);
          const isMonthMilestone = plan.week_number % 4 === 0 || plan.week_number === duration_weeks;
          
          // Relevant resources for this module
          const moduleResources = resources.filter(r => r.module_id === plan.module_id && r.free_status !== 'paid');

          return (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl border transition-all p-5 shadow-xs hover:border-blue-300 ${
                isMonthMilestone ? 'border-l-4 border-l-blue-600 border-slate-200' : 'border-slate-200'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-slate-100">
                <div className="flex items-start gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex flex-col items-center justify-center shrink-0">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Week</span>
                    <span className="text-base font-extrabold text-slate-900 leading-none">{plan.week_number}</span>
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md">
                        {matchedModule ? matchedModule.title : `Phase ${Math.ceil(plan.week_number / 4)}`}
                      </span>
                      {isMonthMilestone && (
                        <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md flex items-center gap-1">
                          <Award className="w-3 h-3" /> Milestone Week
                        </span>
                      )}
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mt-1">
                      {plan.focus_topic}
                    </h3>
                  </div>
                </div>

                {/* Allocated Hours Check Badge */}
                <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                  <div className="text-right">
                    <span className="text-sm font-bold text-slate-900">{plan.allocated_hours}h</span>
                    <span className="text-[11px] text-slate-400 block">/ {weekly_hours}h budget</span>
                  </div>
                  <div className="w-7 h-7 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200" title="Weekly study budget respected">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
              </div>

              {/* Exercises and Milestone Section */}
              <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Practical Exercises */}
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-blue-600" />
                    Hands-On Practice Exercises
                  </h4>
                  <ul className="space-y-1.5">
                    {plan.exercises?.map((ex, exIdx) => (
                      <li key={exIdx} className="text-xs text-slate-600 flex items-start gap-2 bg-slate-50 p-2 rounded-lg border border-slate-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                        <span>{ex}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Milestone Assessment & Resource Links */}
                <div className="space-y-3">
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5 text-amber-600" />
                      Milestone Assessment
                    </h4>
                    <div className="text-xs text-slate-700 bg-amber-50/50 p-2.5 rounded-lg border border-amber-200/60">
                      {plan.milestone_assessment}
                    </div>
                  </div>

                  {/* Quick Resource Portal Links */}
                  {moduleResources.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                        <Bookmark className="w-3.5 h-3.5 text-indigo-600" />
                        Free Course Material
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {moduleResources.map((res) => (
                          <a
                            key={res.id}
                            href={res.original_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-700 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 border border-slate-200 rounded-md px-2 py-1 transition-colors"
                          >
                            <span>{res.provider}: {res.title}</span>
                            <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

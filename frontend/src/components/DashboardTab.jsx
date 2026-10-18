import React from 'react';
import {
  Clock, Calendar, BookOpen, ShieldCheck, CheckCircle2,
  AlertCircle, ArrowRight, Sparkles, RefreshCw, FileText, Check, Download
} from 'lucide-react';
import { getRoadmapMarkdownDownloadUrl } from '../api';

export default function DashboardTab({
  learningPath,
  onNavigateTab,
  onRefresh,
  isRefreshing
}) {
  if (!learningPath) {
    return (
      <div className="text-center py-20 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <Sparkles className="w-12 h-12 text-blue-500 mx-auto mb-3 opacity-60" />
        <h3 className="text-lg font-semibold text-slate-800">No Learning Path Active</h3>
        <p className="text-slate-500 text-sm max-w-md mx-auto mt-1 mb-4">
          Click "Quick Start (6mo/5h)" or "New Goal" above to build your first AI-curated, verified roadmap.
        </p>
      </div>
    );
  }

  const {
    goal,
    starting_level,
    weekly_hours,
    duration_weeks,
    total_available_hours,
    feasibility_status,
    feasibility_notes,
    modules = [],
    weekly_plans = [],
    resources = [],
    proposed_actions = [],
    study_sessions = []
  } = learningPath;

  const totalAllocated = weekly_plans.reduce((sum, p) => sum + (p.allocated_hours || 0), 0);
  const pendingActions = proposed_actions.filter(a => a.approval_status === 'Pending Approval');
  const verifiedResources = resources.filter(r => r.free_status === 'verified_free');
  const activeReplacements = resources.filter(r => r.is_replacement);

  return (
    <div className="space-y-6">
      {/* Top Hero Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-radial from-blue-50 to-transparent opacity-60 pointer-events-none -mr-20 -mt-20" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded-full font-semibold">
                {starting_level} Level
              </span>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                feasibility_status === 'feasible' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {feasibility_status === 'feasible' ? 'Scope Feasible' : 'Constrained Scope'}
              </span>
              <span className="text-xs text-slate-400">ID: {learningPath.id}</span>
            </div>
            
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              {goal}
            </h1>
            
            <p className="text-slate-600 text-sm mt-1 max-w-2xl">
              Personalized {duration_weeks}-week roadmap balanced at {weekly_hours} hours/week using 100% verified free public courses, interactive sandboxes, and documentation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <a
              href={getRoadmapMarkdownDownloadUrl(learningPath.id)}
              download={`roadmap_${learningPath.id}.md`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors shadow-2xs"
              title="Download full roadmap as Markdown documentation"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export (.md)</span>
            </a>

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => onNavigateTab('learning_path')}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-xs transition-colors"
            >
              <span>View Timeline</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Feasibility Alert */}
        {feasibility_notes && (
          <div className="mt-5 p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-2.5 text-xs text-slate-700">
            <AlertCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-900">Curriculum Architecture Rationale: </span>
              {feasibility_notes}
            </div>
          </div>
        )}
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Available Hours */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-slate-500">Total Budget</span>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-slate-900">{total_available_hours}</span>
            <span className="text-xs text-slate-500 font-medium">hours</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
            <span>{duration_weeks} wks × {weekly_hours}h/wk</span>
            <span className="text-emerald-700 font-medium">{totalAllocated.toFixed(0)}h planned</span>
          </div>
        </div>

        {/* Learning Modules */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-slate-500">Modules Ordered</span>
            <BookOpen className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-slate-900">{modules.length}</span>
            <span className="text-xs text-slate-500 font-medium">stages</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Prerequisite ordered</p>
        </div>

        {/* Verified Free Resources */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-slate-500">Free Resources</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-slate-900">{verifiedResources.length}</span>
            <span className="text-xs text-slate-500 font-medium">verified</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
            <span>0 paid / 0 broken</span>
            {activeReplacements.length > 0 && (
              <span className="text-blue-700 font-medium">{activeReplacements.length} replaced</span>
            )}
          </div>
        </div>

        {/* Pending Actions for Human Approval */}
        <div className={`rounded-xl border p-4 shadow-xs transition-all ${
          pendingActions.length > 0 ? 'bg-amber-50/50 border-amber-200' : 'bg-white border-slate-200'
        }`}>
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium text-slate-600">Pending Approvals</span>
            <Calendar className="w-4 h-4 text-amber-600" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-slate-900">{pendingActions.length}</span>
            <span className="text-xs text-slate-500 font-medium">actions</span>
          </div>
          <button
            onClick={() => onNavigateTab('approval_center')}
            className="text-[11px] text-blue-600 hover:text-blue-800 font-semibold mt-1 flex items-center gap-1"
          >
            Review actions <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Two Column Section: Modules Progression & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Prerequisite-Ordered Modules Roadmap */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Curriculum Progression</h2>
              <p className="text-xs text-slate-500">Ordered by strict prerequisite dependency graph</p>
            </div>
            <button
              onClick={() => onNavigateTab('learning_path')}
              className="text-xs text-blue-600 font-semibold hover:underline"
            >
              See all {weekly_plans.length} weeks
            </button>
          </div>

          <div className="space-y-3">
            {modules.map((mod, idx) => (
              <div
                key={mod.id}
                className="p-3.5 rounded-xl border border-slate-200 hover:border-blue-200 transition-all bg-slate-50/50"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900">{mod.title}</h4>
                      <p className="text-xs text-slate-600 mt-0.5">{mod.description}</p>
                      
                      {/* Skills Badges */}
                      <div className="flex flex-wrap gap-1 mt-2">
                        {mod.skills_covered?.map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className="bg-white text-slate-700 border border-slate-200 text-[10px] px-2 py-0.5 rounded-md font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <span className="text-xs font-semibold text-slate-500 shrink-0">
                    ~{mod.estimated_hours}h
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 1 Col: Agent Verification & Actions Summary */}
        <div className="space-y-4">
          {/* Approval Callout */}
          <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-blue-300">
              <ShieldCheck className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Human-in-the-Loop</span>
            </div>
            <h3 className="font-bold text-base mb-1">Approval Center Controls</h3>
            <p className="text-slate-300 text-xs mb-4">
              All calendar blocks and course enrollments require explicit human approval prior to execution.
            </p>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-300 border-b border-slate-800 pb-1.5">
                <span>Pending Enrollment Actions:</span>
                <span className="font-bold text-white">
                  {proposed_actions.filter(a => a.action_type === 'course_enrollment' && a.approval_status === 'Pending Approval').length}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-300 border-b border-slate-800 pb-1.5">
                <span>Pending Calendar Blocks:</span>
                <span className="font-bold text-white">
                  {proposed_actions.filter(a => a.action_type === 'calendar_block' && a.approval_status === 'Pending Approval').length}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-300 pb-1">
                <span>Approved & Synced:</span>
                <span className="font-bold text-emerald-400">
                  {proposed_actions.filter(a => a.approval_status === 'Approved').length}
                </span>
              </div>
            </div>
            <button
              onClick={() => onNavigateTab('approval_center')}
              className="w-full mt-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition-colors"
            >
              Open Approval Center
            </button>
          </div>

          {/* Test Lab Shortcut */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <h3 className="font-bold text-sm text-slate-900 mb-1">Official Test Lab</h3>
            <p className="text-xs text-slate-500 mb-3">
              Automated tests for TC1 (Budget & Prereqs), TC2 (Paid Course), TC3 (Broken Link), and TC4 (Idempotent Rerun).
            </p>
            <button
              onClick={() => onNavigateTab('test_lab')}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5 text-blue-600" />
              <span>Run Benchmark Test Suite</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

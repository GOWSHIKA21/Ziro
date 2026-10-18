import React from 'react';
import { Compass, PlusCircle, Play, User, LogOut, Lock } from 'lucide-react';

export default function Navbar({
  learningPaths,
  activePath,
  currentUser,
  onSelectPath,
  onOpenNewModal,
  onQuickStart,
  onOpenAuthModal,
  onLogout
}) {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
              <Compass className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">Free Learning Path Builder</span>
                <span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full font-medium border border-blue-200">
                  AI Agent
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Autonomous verified roadmap generator with human approval controls
              </p>
            </div>
          </div>

          {/* Center: Path Selector */}
          {learningPaths && learningPaths.length > 0 && (
            <div className="hidden lg:flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Active Path:</span>
              <select
                className="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-blue-500 max-w-xs truncate"
                value={activePath?.id || ''}
                onChange={(e) => onSelectPath(e.target.value)}
              >
                {learningPaths.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.goal} ({p.duration_weeks}w @ {p.weekly_hours}h/wk)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Right Action Buttons */}
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={onQuickStart}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs sm:text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors shadow-2xs"
              title="Run official example: Data Analyst in 6 months with 5h/week"
            >
              <Play className="w-3.5 h-3.5 fill-blue-600 text-blue-600" />
              <span className="hidden sm:inline">Quick Start (6mo/5h)</span>
              <span className="sm:hidden">Benchmark</span>
            </button>

            <button
              onClick={onOpenNewModal}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-2xs transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>New Goal</span>
            </button>

            {/* User Profile / Auth Button */}
            {currentUser ? (
              <div className="flex items-center gap-2 pl-1 border-l border-slate-200">
                <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 text-slate-700 text-xs font-semibold">
                  <User className="w-3.5 h-3.5 text-blue-600" />
                  <span className="max-w-[100px] truncate">{currentUser.full_name || currentUser.email}</span>
                </div>
                <button
                  onClick={onLogout}
                  title="Log Out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuthModal}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs sm:text-sm font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
              >
                <Lock className="w-3.5 h-3.5 text-slate-500" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

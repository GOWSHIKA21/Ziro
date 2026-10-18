import React, { useState } from 'react';
import { GitFork, CheckCircle2, Lock, ArrowRight, BookOpen, Clock, Award } from 'lucide-react';

export default function SkillGraphTab({ learningPath }) {
  const [selectedModule, setSelectedModule] = useState(null);

  if (!learningPath || !learningPath.modules || learningPath.modules.length === 0) {
    return (
      <div className="p-8 text-center bg-white rounded-3xl border border-slate-200">
        <p className="text-sm text-slate-500">No skill modules available yet. Generate a learning path first.</p>
      </div>
    );
  }

  const modules = learningPath.modules;
  const activeModule = selectedModule || modules[0];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <GitFork className="w-4 h-4" />
            </span>
            <h2 className="text-lg font-bold text-slate-900">Skill Dependency DAG & Prerequisite Map</h2>
          </div>
          <p className="text-xs text-slate-500">
            Interactive prerequisite graph ensuring foundational competencies are mastered before advanced specializations.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200">
          <Award className="w-4 h-4 text-amber-500" />
          <span>{modules.length} Connected Skill Milestones</span>
        </div>
      </div>

      {/* Interactive Visual Graph & Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graph Flow (Left 2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Sequential Learning Flow (Click to Inspect)
          </h3>

          <div className="space-y-3">
            {modules.map((mod, idx) => {
              const isSelected = activeModule.id === mod.id;
              const hasPrereqs = mod.prerequisites && mod.prerequisites.length > 0;

              return (
                <div key={mod.id} className="relative">
                  {idx > 0 && (
                    <div className="flex justify-center -my-2 py-1">
                      <div className="w-0.5 h-6 bg-blue-200" />
                    </div>
                  )}

                  <div
                    onClick={() => setSelectedModule(mod)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/50 shadow-md ring-1 ring-blue-500'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                        idx === 0
                          ? 'bg-emerald-500 text-white shadow-xs'
                          : 'bg-slate-900 text-white'
                      }`}>
                        {idx + 1}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">{mod.title}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[11px] text-slate-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            ~{mod.estimated_hours}h
                          </span>
                          {hasPrereqs && (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                              Requires: {mod.prerequisites[0]}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                        idx === 0
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {idx === 0 ? 'Foundation' : 'Specialization'}
                      </span>
                      <ArrowRight className={`w-4 h-4 transition-transform ${isSelected ? 'translate-x-1 text-blue-600' : 'text-slate-400'}`} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Skill Module Inspector (Right 1 col) */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="space-y-5">
            <div className="border-b border-slate-100 pb-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-1 rounded-md">
                Selected Skill Milestone
              </span>
              <h3 className="text-base font-bold text-slate-900 mt-2">{activeModule.title}</h3>
              <p className="text-xs text-slate-500 mt-1">{activeModule.description}</p>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-700 mb-2">Prerequisite Requirements</h4>
              {activeModule.prerequisites && activeModule.prerequisites.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {activeModule.prerequisites.map((p, i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
                      ✓ {p}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-emerald-600 font-semibold">
                  None (Foundational Entry Point)
                </p>
              )}
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-700 mb-2">Competencies & Skills Taught</h4>
              <div className="flex flex-wrap gap-1.5">
                {activeModule.skills_covered?.map((s, i) => (
                  <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-700 mb-2">Measurable Learning Outcomes</h4>
              <ul className="space-y-1.5">
                {activeModule.learning_outcomes?.map((o, i) => (
                  <li key={i} className="text-xs text-slate-600 flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{o}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Estimated Commitment:</span>
            <span className="font-bold text-slate-900">{activeModule.estimated_hours} Hours</span>
          </div>
        </div>
      </div>
    </div>
  );
}

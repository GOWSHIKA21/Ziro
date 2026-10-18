import React, { useState } from 'react';
import {
  Activity, CheckCircle2, Clock, AlertTriangle, ChevronDown,
  ChevronRight, Terminal, Layers, ShieldCheck, Calendar, ArrowRight
} from 'lucide-react';

export default function AgentActivityTab({ learningPath }) {
  const [expandedLogId, setExpandedLogId] = useState(null);

  if (!learningPath) return null;
  const { agent_logs = [], status } = learningPath;

  const STAGES = [
    { id: 'Stage A', name: 'Stage A: Goal Analysis', desc: 'Identify skills & create prerequisite-ordered modules' },
    { id: 'Stage B', name: 'Stage B: Resource Discovery', desc: 'Find public, verified free courses and documentation' },
    { id: 'Stage C', name: 'Stage C: Prerequisite-Aware Planning', desc: 'Construct week-by-week timeline within time budget' },
    { id: 'Stage D', name: 'Stage D: Resource Verification', desc: 'Inspect paywalls, test HTTP status, find replacements' },
    { id: 'Stage E', name: 'Stage E: Action Proposal', desc: 'Prepare enrollments and calendar blocks for approval' },
    { id: 'Stage F', name: 'Stage F: Execution & Verification', desc: 'Idempotent calendar sync & enrollment tracking' }
  ];

  const toggleExpand = (logId) => {
    setExpandedLogId(expandedLogId === logId ? null : logId);
  };

  return (
    <div className="space-y-6">
      {/* Workflow Stages Pipeline Visualizer */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">
              Traceable Workflow Pipeline
            </span>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-1">
              Autonomous Agent Lifecycle
            </h2>
          </div>
          <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full border border-emerald-200">
            Pipeline Active ({status})
          </span>
        </div>

        {/* Stages Stepper */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {STAGES.map((stg, idx) => {
            const hasPassed = agent_logs.some(l => l.stage.includes(stg.id));
            const hasWarning = agent_logs.some(l => l.stage.includes(stg.id) && l.status === 'warning');

            return (
              <div
                key={stg.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  hasWarning
                    ? 'bg-amber-50/50 border-amber-200'
                    : hasPassed
                    ? 'bg-emerald-50/40 border-emerald-200'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Step {idx + 1}</span>
                  {hasWarning ? (
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                  ) : hasPassed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Clock className="w-4 h-4 text-slate-400" />
                  )}
                </div>
                <h4 className="text-xs font-bold text-slate-900 line-clamp-1">{stg.name}</h4>
                <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-2">{stg.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real-Time Agent Audit Log Stream */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-700" />
            <h3 className="font-bold text-sm text-slate-900">Agent Traceability Logs ({agent_logs.length} entries)</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">Immutable Audit Trail</span>
        </div>

        <div className="divide-y divide-slate-100">
          {agent_logs.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No agent events recorded yet.
            </div>
          ) : (
            agent_logs.map((log) => {
              const isExpanded = expandedLogId === log.id;
              const isCompleted = log.status === 'completed';
              const isWarning = log.status === 'warning';
              const isFailed = log.status === 'failed';

              return (
                <div key={log.id} className="p-4 hover:bg-slate-50/50 transition-colors">
                  <div
                    onClick={() => toggleExpand(log.id)}
                    className="flex items-start justify-between gap-3 cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">
                        {isCompleted && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                        {isWarning && <AlertTriangle className="w-4 h-4 text-amber-600" />}
                        {isFailed && <AlertTriangle className="w-4 h-4 text-rose-600" />}
                        {!isCompleted && !isWarning && !isFailed && <Clock className="w-4 h-4 text-blue-500" />}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-slate-900">{log.stage}</span>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize ${
                            isCompleted ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                            isWarning ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            {log.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 mt-1">{log.message}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] text-slate-400 font-mono">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expandable JSON Details */}
                  {isExpanded && log.details && (
                    <div className="mt-3 pl-7">
                      <div className="bg-slate-900 text-slate-200 p-3 rounded-xl font-mono text-[11px] overflow-x-auto max-h-56">
                        <pre>{JSON.stringify(log.details, null, 2)}</pre>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

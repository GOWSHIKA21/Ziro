import React, { useState } from 'react';
import {
  FlaskConical, CheckCircle2, XCircle, Play, RefreshCw,
  Clock, ShieldCheck, ChevronDown, ChevronRight, Terminal, Layers
} from 'lucide-react';

export default function TestLabTab({
  testRuns = [],
  onExecuteTests,
  isExecuting
}) {
  const [selectedScenario, setSelectedScenario] = useState('ALL');
  const [expandedRunId, setExpandedRunId] = useState(null);

  const OFFICIAL_SCENARIOS = [
    {
      id: 'TC1',
      title: 'TC1 — Six Months at Five Hours per Week',
      description: 'Input: Goal = Data Analyst, Level = Beginner, Weekly = 5h, Duration = 26 weeks (~130h). Verifies weekly budget and prerequisite skill ordering.'
    },
    {
      id: 'TC2',
      title: 'TC2 — Course Has Become Paid',
      description: 'Simulates a previously free course becoming paywalled ($49/mo). Verifies detection, evidence logging, autonomous free replacement, and re-verification.'
    },
    {
      id: 'TC3',
      title: 'TC3 — Broken Link',
      description: 'Simulates a course URL returning HTTP 404 Not Found. Verifies failure logging, finding a suitable replacement, and updating roadmap only when verified.'
    },
    {
      id: 'TC4',
      title: 'TC4 — Rerun Without Duplicates',
      description: 'Runs the exact same request twice. Verifies 0 duplicate calendar events, 0 duplicate actions, and exact session ID preservation.'
    }
  ];

  const handleRun = (scenarioId) => {
    onExecuteTests(scenarioId);
  };

  const toggleExpand = (id) => {
    setExpandedRunId(expandedRunId === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Runner Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md flex items-center gap-1">
              <FlaskConical className="w-3.5 h-3.5" /> Mandatory Test Verification Suite
            </span>
            <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
              Deterministic & Reproducible
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Official Scenario Test Lab (TC1–TC4)
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Execute and inspect actual outcomes, verification evidence, and programmatic assertions.
          </p>
        </div>

        {/* Run All Button */}
        <button
          onClick={() => handleRun('ALL')}
          disabled={isExecuting}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-xl shadow-xs transition-colors shrink-0 disabled:opacity-50"
        >
          {isExecuting ? (
            <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
          ) : (
            <Play className="w-4 h-4 fill-white" />
          )}
          <span>Run All 4 Scenarios</span>
        </button>
      </div>

      {/* Scenario Overview Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {OFFICIAL_SCENARIOS.map((scen) => {
          const latestRun = testRuns.find(r => r.scenario_id === scen.id);
          const hasPassed = latestRun?.status === 'passed';
          const hasFailed = latestRun?.status === 'failed';

          return (
            <div
              key={scen.id}
              className={`bg-white rounded-2xl border p-5 shadow-xs transition-all flex flex-col justify-between ${
                hasPassed ? 'border-emerald-200' : hasFailed ? 'border-rose-200' : 'border-slate-200'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-900 bg-slate-100 px-2.5 py-0.5 rounded-md">
                    {scen.id}
                  </span>

                  {latestRun && (
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                      hasPassed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {hasPassed ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {latestRun.status.toUpperCase()} ({latestRun.execution_duration_ms}ms)
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-sm text-slate-900 mb-1">{scen.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{scen.description}</p>
              </div>

              <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  {latestRun ? `Last executed: ${new Date(latestRun.created_at).toLocaleTimeString()}` : 'Not run yet in this session'}
                </span>
                <button
                  onClick={() => handleRun(scen.id)}
                  disabled={isExecuting}
                  className="px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  <Play className="w-3 h-3 fill-blue-600" />
                  <span>Run {scen.id}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Test Execution Results Table & Evidence Inspector */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-700" />
            <h3 className="font-bold text-sm text-slate-900">
              Scenario Execution Evidence & Results ({testRuns.length} recorded)
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">Real Test Evidence Logs</span>
        </div>

        <div className="divide-y divide-slate-100">
          {testRuns.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No test scenarios executed yet. Click "Run All 4 Scenarios" above to run the suite.
            </div>
          ) : (
            testRuns.map((run) => {
              const isExpanded = expandedRunId === run.id;
              const isPassed = run.status === 'passed';

              return (
                <div key={run.id} className="p-5 hover:bg-slate-50/50 transition-colors">
                  <div
                    onClick={() => toggleExpand(run.id)}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">
                        {isPassed ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                        ) : (
                          <XCircle className="w-5 h-5 text-rose-600" />
                        )}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded">
                            {run.scenario_id}
                          </span>
                          <span className="font-bold text-sm text-slate-900">{run.scenario_name}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            isPassed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}>
                            {run.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1 line-clamp-1">
                          <span className="font-semibold text-slate-700">Actual: </span>
                          {run.actual_result}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                      <span className="text-xs text-slate-400 font-mono">
                        {run.execution_duration_ms}ms • {new Date(run.created_at).toLocaleTimeString()}
                      </span>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Diff & Evidence */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-100 space-y-3 text-xs pl-8">
                      {/* Expected Result */}
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                        <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px] block mb-1">
                          Expected Outcome
                        </span>
                        <p className="text-slate-700">{run.expected_result}</p>
                      </div>

                      {/* Actual Result */}
                      <div className="bg-blue-50/50 p-3 rounded-xl border border-blue-200/60">
                        <span className="font-bold text-blue-900 uppercase tracking-wider text-[10px] block mb-1">
                          Actual Outcome
                        </span>
                        <p className="text-blue-950 font-medium">{run.actual_result}</p>
                      </div>

                      {/* Verification Evidence JSON */}
                      {run.verification_evidence && (
                        <div>
                          <span className="font-bold text-slate-600 uppercase tracking-wider text-[10px] block mb-1">
                            Verification Evidence JSON
                          </span>
                          <div className="bg-slate-900 text-slate-200 p-3.5 rounded-xl font-mono text-[11px] overflow-x-auto max-h-56">
                            <pre>{JSON.stringify(run.verification_evidence, null, 2)}</pre>
                          </div>
                        </div>
                      )}
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

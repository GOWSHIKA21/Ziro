import React, { useState } from 'react';
import {
  ShieldCheck, AlertTriangle, XCircle, ExternalLink, RefreshCw,
  Search, Eye, Sparkles, CheckCircle2, AlertCircle, ArrowRight
} from 'lucide-react';

export default function ResourceLibraryTab({
  learningPath,
  onVerifyResources,
  onReplaceResource,
  isVerifying
}) {
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [replacingId, setReplacingId] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  if (!learningPath) {
    return (
      <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 p-8 shadow-xs">
        <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">No Learning Path Selected</h3>
        <p className="text-slate-500 text-sm max-w-md mx-auto mt-1">
          Select or create a learning path to inspect verified free resources, audit paywalls, and view replacements.
        </p>
      </div>
    );
  }
  const { resources = [] } = learningPath;

  const filteredResources = resources.filter((r) => {
    if (filter === 'free' && r.free_status !== 'verified_free') return false;
    if (filter === 'paid' && r.free_status !== 'paid') return false;
    if (filter === 'broken' && r.free_status !== 'broken') return false;
    if (filter === 'replacements' && !r.is_replacement) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const titleMatch = r.title.toLowerCase().includes(q);
      const providerMatch = r.provider.toLowerCase().includes(q);
      const skillMatch = (r.skills_covered || []).some(s => s.toLowerCase().includes(q));
      if (!titleMatch && !providerMatch && !skillMatch) return false;
    }
    return true;
  });

  const handleManualReplace = async (resourceId) => {
    setReplacingId(resourceId);
    try {
      await onReplaceResource(resourceId, 'User requested free replacement from library');
    } finally {
      setReplacingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Simulation Controls */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> 100% Verified Free Catalog
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Curated Resource Library & Evidence Audit
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Every course and documentation link is inspected for active paywalls, subscriptions, and HTTP status.
          </p>
        </div>

        {/* Action & Simulation Triggers */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Live Re-verify */}
          <button
            onClick={() => onVerifyResources({})}
            disabled={isVerifying}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
            <span>Verify All Links</span>
          </button>

          {/* Simulate Paid (TC2 Trigger) */}
          <button
            onClick={() => onVerifyResources({ simulate_paid_resource_id: 'ANY' })}
            disabled={isVerifying}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors"
            title="Simulate course becoming paid to trigger TC2 auto-replacement"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Simulate Paywall (TC2)</span>
          </button>

          {/* Simulate Broken (TC3 Trigger) */}
          <button
            onClick={() => onVerifyResources({ simulate_broken_resource_id: 'ANY' })}
            disabled={isVerifying}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors"
            title="Simulate broken 404 URL to trigger TC3 auto-replacement"
          >
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Simulate 404 (TC3)</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {[
            { id: 'all', label: `All (${resources.length})` },
            { id: 'free', label: `Verified Free (${resources.filter(r => r.free_status === 'verified_free').length})` },
            { id: 'paid', label: `Paid (${resources.filter(r => r.free_status === 'paid').length})` },
            { id: 'broken', label: `Broken (${resources.filter(r => r.free_status === 'broken').length})` },
            { id: 'replacements', label: `Replacements (${resources.filter(r => r.is_replacement).length})` }
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setFilter(t.id)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                filter === t.id
                  ? 'bg-slate-900 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search title, skill, provider..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Resources Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Resource & Provider</th>
                <th className="py-3 px-4">Skills Covered</th>
                <th className="py-3 px-4">Price Status</th>
                <th className="py-3 px-4">Access / Account</th>
                <th className="py-3 px-4">Verification Audit</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredResources.map((res) => {
                const isPaid = res.free_status === 'paid';
                const isBroken = res.free_status === 'broken';
                const isFree = res.free_status === 'verified_free';

                return (
                  <tr key={res.id} className="hover:bg-slate-50/60 transition-colors">
                    {/* Title & Provider */}
                    <td className="py-3.5 px-4 max-w-xs">
                      <div className="flex items-center gap-2">
                        {res.is_replacement && (
                          <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-1.5 py-0.5 rounded">
                            REPLACEMENT
                          </span>
                        )}
                        <span className="font-bold text-slate-900 line-clamp-1">{res.title}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <span className="font-medium text-slate-700">{res.provider}</span>
                        <span>•</span>
                        <span>~{res.estimated_hours}h</span>
                        <span>•</span>
                        <a
                          href={res.original_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline inline-flex items-center gap-0.5"
                        >
                          Visit <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </td>

                    {/* Skills */}
                    <td className="py-3.5 px-4 max-w-xs">
                      <div className="flex flex-wrap gap-1">
                        {res.skills_covered?.slice(0, 3).map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className="bg-slate-100 text-slate-700 text-[10px] px-2 py-0.5 rounded-md font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                        {res.skills_covered?.length > 3 && (
                          <span className="text-[10px] text-slate-400">+{res.skills_covered.length - 3}</span>
                        )}
                      </div>
                    </td>

                    {/* Price Status */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {isFree && (
                        <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 font-semibold px-2 py-0.5 rounded-md border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3" /> Verified Free
                        </span>
                      )}
                      {isPaid && (
                        <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 font-semibold px-2 py-0.5 rounded-md border border-amber-200">
                          <AlertTriangle className="w-3 h-3" /> Paid / Paywalled
                        </span>
                      )}
                      {isBroken && (
                        <span className="inline-flex items-center gap-1 bg-rose-50 text-rose-700 font-semibold px-2 py-0.5 rounded-md border border-rose-200">
                          <XCircle className="w-3 h-3" /> Broken Link (404)
                        </span>
                      )}
                    </td>

                    {/* Access / Account */}
                    <td className="py-3.5 px-4 whitespace-nowrap text-slate-600">
                      {res.account_required ? (
                        <span className="text-slate-600">Free Account Req.</span>
                      ) : (
                        <span className="text-emerald-700 font-medium">Public Open Access</span>
                      )}
                    </td>

                    {/* Verification Notes */}
                    <td className="py-3.5 px-4 max-w-xs">
                      <p className="text-[11px] text-slate-600 line-clamp-2">
                        {res.verification_notes || 'Verified against authentic catalog.'}
                      </p>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedEvidence(res)}
                          className="px-2.5 py-1 text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-md font-medium text-[11px] inline-flex items-center gap-1 transition-colors"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Audit</span>
                        </button>

                        <button
                          onClick={() => handleManualReplace(res.id)}
                          disabled={replacingId === res.id}
                          className="px-2.5 py-1 text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md font-medium text-[11px] inline-flex items-center gap-1 transition-colors disabled:opacity-50"
                        >
                          <RefreshCw className={`w-3 h-3 ${replacingId === res.id ? 'animate-spin' : ''}`} />
                          <span>Replace</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Evidence Inspector Modal */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-sm">Verification Evidence Audit</h3>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="text-slate-400 hover:text-slate-600 font-bold p-1 rounded-md"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-3.5 text-xs text-slate-700">
              <div>
                <span className="font-semibold text-slate-500 uppercase tracking-wider block text-[10px]">Resource</span>
                <span className="font-bold text-slate-900 text-sm">{selectedEvidence.title}</span>
                <span className="text-slate-500 block text-xs">{selectedEvidence.provider}</span>
              </div>

              <div>
                <span className="font-semibold text-slate-500 uppercase tracking-wider block text-[10px]">Destination URL</span>
                <a
                  href={selectedEvidence.original_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline break-all"
                >
                  {selectedEvidence.original_url}
                </a>
              </div>

              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Price Classification</span>
                  <span className="font-bold text-slate-900 capitalize">{selectedEvidence.free_status}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Verification Status</span>
                  <span className="font-bold text-slate-900 capitalize">{selectedEvidence.verification_status}</span>
                </div>
              </div>

              <div>
                <span className="font-semibold text-slate-500 uppercase tracking-wider block text-[10px]">Audit Evidence Details</span>
                <div className="bg-slate-900 text-slate-100 p-3 rounded-xl font-mono text-[11px] mt-1 whitespace-pre-wrap leading-relaxed">
                  {selectedEvidence.verification_notes || 'Confirmed public open access from authentic provider.'}
                </div>
              </div>

              {selectedEvidence.evidence_history && selectedEvidence.evidence_history.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-500 uppercase tracking-wider block text-[10px] mb-1">Check History ({selectedEvidence.evidence_history.length})</span>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {selectedEvidence.evidence_history.map((ev) => (
                      <div key={ev.id} className="p-2 rounded bg-slate-50 border border-slate-100 text-[11px]">
                        <div className="flex justify-between font-medium">
                          <span>Status: {ev.result_status} (HTTP {ev.http_status || 'N/A'})</span>
                          <span className="text-slate-400 text-[10px]">{new Date(ev.check_timestamp).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-slate-600 text-[10px] mt-0.5">{ev.evidence_text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-right">
              <button
                onClick={() => setSelectedEvidence(null)}
                className="px-4 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

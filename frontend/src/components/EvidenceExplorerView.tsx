import { useState, useEffect } from 'react';
import type { FC } from 'react';
import {
  Share2,
  CheckCircle2,
  AlertTriangle,
  Info,
  Database,
  FileText,
  ShieldCheck,
  RefreshCw,
  Search
} from 'lucide-react';
import type { EvidenceGraphResponse } from '../types';
import { fetchRecentEvidence, fetchEvidenceRecord } from '../api';

interface EvidenceExplorerViewProps {
  initialDecisionId?: string | null;
}

export const EvidenceExplorerView: FC<EvidenceExplorerViewProps> = ({ initialDecisionId }) => {
  const [recentDecisions, setRecentDecisions] = useState<any[]>([]);
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(initialDecisionId || null);
  const [graphData, setGraphData] = useState<EvidenceGraphResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load recent decisions list on mount
  useEffect(() => {
    fetchRecentEvidence(15)
      .then((records) => {
        setRecentDecisions(records);
        if (!selectedDecisionId && records.length > 0) {
          setSelectedDecisionId(records[0].decision_id);
        }
      })
      .catch((err) => console.warn('Failed to load recent evidence records:', err));
  }, []);

  // When selectedDecisionId changes, fetch full graph
  useEffect(() => {
    if (!selectedDecisionId) return;
    setLoading(true);
    setErrorMsg(null);
    fetchEvidenceRecord(selectedDecisionId)
      .then((data) => setGraphData(data))
      .catch((err) => setErrorMsg(err.message || 'Failed to fetch evidence graph details.'))
      .finally(() => setLoading(false));
  }, [selectedDecisionId]);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f766e', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
          <Share2 className="w-4 h-4" />
          <span>The Medicine Evidence Graph</span>
        </div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
          Deterministic Multi-Node Traceability Explorer
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '780px' }}>
          Inspect the complete immutable evidence chain connecting patient query, extracted clinical attributes, official catalogue records, deterministic verification checks, price provenance, and final savings eligibility.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', alignItems: 'flex-start' }}>
        {/* Left Sidebar: Recent Decisions in SQLite */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '1rem', maxHeight: '700px', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-primary)', textTransform: 'uppercase' }}>
              Stored Decisions ({recentDecisions.length})
            </span>
            <button
              type="button"
              onClick={() => {
                fetchRecentEvidence(15).then(setRecentDecisions);
              }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              title="Refresh SQLite Evidence List"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {recentDecisions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No decisions recorded yet. Run a search or verification to populate the graph.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {recentDecisions.map((rec) => {
                const isSelected = selectedDecisionId === rec.decision_id;
                const isVerified = rec.verification_status === 'VERIFIED_FOR_PRICE_COMPARISON';
                return (
                  <div
                    key={rec.decision_id}
                    onClick={() => setSelectedDecisionId(rec.decision_id)}
                    style={{
                      background: isSelected ? 'var(--bg-app)' : 'none',
                      border: `1px solid ${isSelected ? 'var(--accent)' : 'transparent'}`,
                      borderRadius: 'var(--radius-md)',
                      padding: '0.65rem 0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#0f766e' }}>
                        {rec.decision_id}
                      </span>
                      <span
                        style={{
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          padding: '0.1rem 0.35rem',
                          borderRadius: 'var(--radius-sm)',
                          background: isVerified ? '#ecfdf5' : '#fffbeb',
                          color: isVerified ? '#065f46' : '#92400e'
                        }}
                      >
                        {isVerified ? 'Verified' : 'Clarify'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.15rem' }}>
                      {rec.query}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {rec.candidate_name}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Main Area: The Connected Evidence Chain */}
        <div>
          {loading ? (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '4rem', textAlign: 'center' }}>
              <RefreshCw className="w-8 h-8 text-teal-600 animate-spin" style={{ margin: '0 auto 1rem auto' }} />
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Loading Evidence Graph Chain...</div>
            </div>
          ) : errorMsg ? (
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-lg)', padding: '1.5rem', color: '#991b1b' }}>
              {errorMsg}
            </div>
          ) : graphData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Decision Header Card */}
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#0f766e', background: '#f0fdfa', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-sm)' }}>
                      Decision Node: {graphData.decision_id}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                      Timestamp: {graphData.decision.verified_at}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.6rem',
                      borderRadius: 'var(--radius-full)',
                      background: graphData.decision.is_savings_eligible ? '#ecfdf5' : '#fffbeb',
                      color: graphData.decision.is_savings_eligible ? '#065f46' : '#92400e',
                      border: `1px solid ${graphData.decision.is_savings_eligible ? '#a7f3d0' : '#fde68a'}`
                    }}
                  >
                    {graphData.decision.verification_status}
                  </span>
                </div>
                <div style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  <b>Summary:</b> {graphData.decision.summary}
                </div>
              </div>

              {/* Connected Visual Pipeline */}
              <div style={{ position: 'relative' }}>
                {/* Node 1: Input Evidence */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                    <Search className="w-4 h-4" />
                    <span>Node 1: Input Evidence ({graphData.input_evidence.input_id})</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
                    <div><b>Query String:</b> "{graphData.input_evidence.query}"</div>
                    <div><b>Input Source:</b> {graphData.input_evidence.input_type}</div>
                    <div><b>Reference Brand:</b> {graphData.input_evidence.reference_brand || 'None stated'}</div>
                    <div><b>User Price Quote:</b> {graphData.input_evidence.user_reported_price_inr ? `₹${graphData.input_evidence.user_reported_price_inr}` : 'Not provided'}</div>
                  </div>
                </div>

                {/* Node 2: Extraction & Normalization */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                    <FileText className="w-4 h-4" />
                    <span>Node 2: Attribute Extraction & Normalization</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
                    <div><b>Normalized:</b> "{graphData.extraction.normalized_query}"</div>
                    <div><b>Detected Molecules:</b> {graphData.extraction.detected_molecules.join(', ') || 'None'}</div>
                    <div><b>Detected Strengths:</b> {graphData.extraction.detected_strengths.join(', ') || 'Unspecified'}</div>
                    <div><b>Brand Alias Applied:</b> {graphData.extraction.brand_alias_applied || 'Direct query'}</div>
                    <div><b>Is Combination:</b> {graphData.extraction.is_combination ? 'Yes' : 'Single Active Salt'}</div>
                  </div>
                </div>

                {/* Node 3: Candidate Catalogue Record */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                    <Database className="w-4 h-4" />
                    <span>Node 3: Candidate Catalogue Record ({graphData.candidate.product_id})</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
                    <div><b>Official Product:</b> {graphData.candidate.name}</div>
                    <div><b>Catalogue Type:</b> {graphData.candidate.catalogue_type}</div>
                    <div><b>Pack Unit:</b> {graphData.candidate.unit_size}</div>
                    <div><b>Catalogue MRP:</b> ₹{graphData.candidate.mrp_inr.toFixed(2)}</div>
                    <div><b>Source Dataset:</b> {graphData.candidate.source_file}</div>
                  </div>
                </div>

                {/* Node 4: Attribute Verification Checks */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Node 4: Clinical Attribute Compatibility Checks ({graphData.attribute_checks.length} checks)</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {graphData.attribute_checks.map((chk, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'var(--bg-app)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          padding: '0.65rem 0.75rem',
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '0.6rem'
                        }}
                      >
                        {chk.is_match ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" style={{ marginTop: '2px' }} />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" style={{ marginTop: '2px' }} />
                        )}
                        <div style={{ flex: 1, fontSize: '0.82rem' }}>
                          <div style={{ fontWeight: 700, textTransform: 'capitalize', color: 'var(--text-primary)' }}>
                            {chk.attribute_name.replace('_', ' ')}: {chk.confidence}
                          </div>
                          <div style={{ color: 'var(--text-secondary)' }}>{chk.details}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Node 5: Price Evidence & Normalization */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                    <Info className="w-4 h-4" />
                    <span>Node 5: Price Provenance & Pack Normalization</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
                    <div><b>Formula Applied:</b> <code>{graphData.savings.formula_applied}</code></div>
                    <div><b>Normalized Unit:</b> {graphData.savings.normalized_unit_basis}</div>
                    <div><b>Reference Price:</b> {graphData.savings.reference_price_inr ? `₹${graphData.savings.reference_price_inr.toFixed(2)}` : 'Unrecorded'}</div>
                    <div><b>Generic Price:</b> {graphData.savings.comparison_price_inr ? `₹${graphData.savings.comparison_price_inr.toFixed(2)}` : 'N/A'}</div>
                    <div><b>Net Difference:</b> {graphData.savings.absolute_saving_inr ? `₹${graphData.savings.absolute_saving_inr.toFixed(2)} (${graphData.savings.percentage_saving}%)` : 'Quarantined'}</div>
                  </div>
                </div>
              </div>

              {/* Audit Provenance Footer */}
              <div style={{ background: 'var(--bg-app)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <b>Audit Trail:</b> Generated by {graphData.software_version}. Verified deterministically against Rajya Sabha Parliamentary benchmark Annexure 1784-B & NPPA DPCO statutory ceiling price schedule.
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '4rem 1rem', color: 'var(--text-muted)', background: 'var(--bg-card)', borderRadius: 'var(--radius-xl)' }}>
              Select a decision from the left list to inspect its complete Evidence Graph.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

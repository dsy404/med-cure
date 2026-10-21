import { useState } from 'react';
import type { FC, FormEvent } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  Info,
  XCircle,
  X,
  PlusCircle,
  ShieldCheck,
  FileText,
  Calculator,
  RefreshCw
} from 'lucide-react';
import type { VerificationResult, MedicineProduct } from '../types';
import { verifyCandidate } from '../api';

interface EvidenceCardProps {
  result: VerificationResult;
  candidateProduct: MedicineProduct;
  onClose: () => void;
  onAddToBasket?: (candidate: MedicineProduct, verification: VerificationResult) => void;
  onOpenEvidenceGraph?: (decisionId: string) => void;
}

export const EvidenceCard: FC<EvidenceCardProps> = ({
  result: initialResult,
  candidateProduct,
  onClose,
  onAddToBasket,
  onOpenEvidenceGraph
}) => {
  const [result, setResult] = useState<VerificationResult>(initialResult);
  const [customPrice, setCustomPrice] = useState<string>('');
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [added, setAdded] = useState<boolean>(false);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED_FOR_PRICE_COMPARISON':
        return {
          icon: <CheckCircle className="w-5 h-5 text-emerald-600" />,
          title: 'Verified for Price Comparison',
          className: 'verified',
          subtext: 'Clinical attributes and price evidence align. Comparison calculation is defensible.'
        };
      case 'NEEDS_CLARIFICATION':
        return {
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
          title: 'Needs Clinical Clarification',
          className: 'needs_clarification',
          subtext: 'Strength, form, or active molecule requires clarification before savings can be confirmed.'
        };
      case 'INCOMPARABLE_PRICE_BASIS':
        return {
          icon: <Info className="w-5 h-5 text-blue-600" />,
          title: 'Incomparable Price Basis',
          className: 'incomparable',
          subtext: 'Statutory ceiling price (NPPA) or unaligned price types cannot be compared directly against retail quotes.'
        };
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return {
          icon: <XCircle className="w-5 h-5 text-rose-600" />,
          title: 'Insufficient Evidence',
          className: 'insufficient',
          subtext: 'Catalogue price is listed as zero or reference retail price is absent.'
        };
    }
  };

  const statusInfo = getStatusBadge(result.verification_status);

  const handleRecalculateWithCustomPrice = async (e: FormEvent) => {
    e.preventDefault();
    const val = parseFloat(customPrice);
    if (isNaN(val) || val <= 0) return;

    setRecalculating(true);
    try {
      const updated = await verifyCandidate(
        result.query,
        candidateProduct.product_id,
        val,
        candidateProduct.unit_size
      );
      setResult(updated);
    } catch (err) {
      console.error('Failed to recalculate with custom price:', err);
    } finally {
      setRecalculating(false);
    }
  };

  const handleAdd = () => {
    if (onAddToBasket) {
      onAddToBasket(candidateProduct, result);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    }
  };

  return (
    <div className="evidence-modal-backdrop" onClick={onClose}>
      <div className="evidence-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <ShieldCheck className="w-6 h-6 text-teal-600" />
            <span>Medicine Match Evidence Card</span>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Query & Matched Product summary */}
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', background: 'var(--bg-canvas)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-md)' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Searched Input</div>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>"{result.query}"</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Catalogue Candidate</div>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0f766e' }}>{result.candidate_name}</div>
              <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>ID: {result.candidate_id} ({result.candidate_catalogue_type})</div>
            </div>
          </div>

          {/* Status Banner */}
          <div className={`status-banner ${statusInfo.className}`}>
            <div style={{ marginTop: '2px' }}>{statusInfo.icon}</div>
            <div>
              <div className="status-headline">{statusInfo.title}</div>
              <div className="status-subtext">{result.plain_language_summary}</div>
            </div>
          </div>

          {/* Attribute Checklist */}
          <div className="checklist-box">
            <div className="checklist-title">Deterministic Attribute Verification</div>
            {result.attribute_checks.map((check, idx) => (
              <div key={idx} className="checklist-row">
                <div>
                  <div className="check-label">{check.attribute_name.replace('_', ' ')}</div>
                  <div className="check-detail">{check.details}</div>
                </div>
                <div>
                  <span className={`check-badge ${check.confidence.toLowerCase()}`}>
                    {check.is_match ? 'Matched' : check.confidence}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Price Evidence Details */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {/* Comparison Generic Record */}
            <div style={{ background: 'var(--bg-canvas)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <FileText className="w-4 h-4 text-teal-600" />
                <span>Catalogue Generic Quote</span>
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f2744' }}>
                ₹{candidateProduct.price.amount_inr}
                <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '0.3rem' }}>
                  per {candidateProduct.unit_size}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                Source: {candidateProduct.price.source_provenance}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontStyle: 'italic' }}>
                {candidateProduct.price.disclaimer}
              </div>
            </div>

            {/* Reference Price Record */}
            <div style={{ background: 'var(--bg-canvas)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <Calculator className="w-4 h-4 text-blue-600" />
                <span>Reference Price Evidence</span>
              </div>
              {result.reference_price_evidence ? (
                <>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f2744' }}>
                    ₹{result.reference_price_evidence.amount_inr}
                    <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '0.3rem' }}>
                      per {result.reference_price_evidence.unit_basis}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                    Source: {result.reference_price_evidence.source_organization}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Record: {result.reference_price_evidence.source_record_id} ({result.reference_price_evidence.effective_or_verified_date})
                  </div>
                </>
              ) : (
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No official branded retail price recorded for this specific strength/pack in government surveyed tables.
                </div>
              )}

              {/* Custom Price Calculator Form */}
              <form onSubmit={handleRecalculateWithCustomPrice} style={{ marginTop: '0.75rem', paddingTop: '0.65rem', borderTop: '1px solid var(--border-subtle)' }}>
                <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Test your pharmacy price (₹):
                </label>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="e.g. 35.00"
                    value={customPrice}
                    onChange={(e) => setCustomPrice(e.target.value)}
                    style={{ flex: 1, padding: '0.3rem 0.5rem', fontSize: '0.82rem', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)' }}
                  />
                  <button
                    type="submit"
                    disabled={recalculating || !customPrice}
                    style={{ background: '#0284c7', color: 'white', border: 'none', padding: '0.3rem 0.7rem', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.2rem' }}
                  >
                    {recalculating ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Compare'}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Deterministic Savings Box */}
          {result.savings.is_eligible && (
            <div className="savings-box">
              <div className="savings-header">
                <span className="savings-title">Verified Potential Monetary Difference</span>
                <span className="savings-big-diff">
                  ₹{result.savings.absolute_saving_inr}
                  <span style={{ fontSize: '1rem', fontWeight: 700, marginLeft: '0.4rem' }}>
                    ({result.savings.percentage_saving}%)
                  </span>
                </span>
              </div>
              <table className="savings-table">
                <tbody>
                  <tr>
                    <td>Standardized Comparison Basis:</td>
                    <td>{result.savings.normalized_unit_basis}</td>
                  </tr>
                  <tr>
                    <td>Reference Price (Normalized):</td>
                    <td>₹{result.savings.reference_price_inr}</td>
                  </tr>
                  <tr>
                    <td>Jan Aushadhi Generic Price (Normalized):</td>
                    <td>₹{result.savings.comparison_price_inr}</td>
                  </tr>
                  <tr>
                    <td>Calculation Formula:</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{result.savings.formula_applied}</td>
                  </tr>
                </tbody>
              </table>
              {result.savings.assumptions.length > 0 && (
                <div style={{ fontSize: '0.75rem', color: '#0f766e', background: 'rgba(255,255,255,0.6)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                  <strong>Assumptions:</strong> {result.savings.assumptions.join(' ')}
                </div>
              )}
            </div>
          )}

          {/* If ineligible, show why */}
          {!result.savings.is_eligible && (
            <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: 'var(--radius-md)', padding: '0.85rem 1rem' }}>
              <div style={{ fontWeight: 700, color: '#9f1239', fontSize: '0.88rem', marginBottom: '0.25rem' }}>
                Confirmed Savings Excluded
              </div>
              <div style={{ fontSize: '0.82rem', color: '#881337', lineHeight: 1.45 }}>
                {result.savings.ineligible_reason || 'Evidence is insufficient or price basis is incompatible for a valid savings calculation.'}
              </div>
            </div>
          )}

          {/* Action Row */}
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            {onAddToBasket && (
              <button
                onClick={handleAdd}
                style={{
                  flex: 1,
                  background: added ? '#059669' : '#0d9488',
                  color: 'white',
                  border: 'none',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'background 0.2s'
                }}
              >
                <PlusCircle className="w-4 h-4" />
                <span>{added ? 'Added to Prescription Basket!' : 'Add to Prescription Basket'}</span>
              </button>
            )}
            {result.decision_id && onOpenEvidenceGraph && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onOpenEvidenceGraph(result.decision_id!);
                }}
                style={{
                  background: 'var(--bg-app)',
                  color: '#0f766e',
                  border: '1px solid #99f6e4',
                  padding: '0.75rem 1.1rem',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: 600,
                  fontSize: '0.88rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem'
                }}
              >
                <span>View Evidence Graph</span>
              </button>
            )}
            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-subtle)',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-subtle)',
                padding: '0.75rem 1.25rem',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer'
              }}
            >
              Done
            </button>
          </div>

          {/* Clinical Disclaimer */}
          <div className="safety-alert">
            <strong>Important Safety Notice:</strong> {result.clinical_disclaimer}
          </div>
        </div>
      </div>
    </div>
  );
};

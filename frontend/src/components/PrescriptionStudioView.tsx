import { useState } from 'react';
import type { FC, FormEvent } from 'react';
import {
  FileText,
  Plus,
  Trash2,
  Download,
  ShieldCheck,
  AlertTriangle,
  Info,
  CheckCircle,
  ExternalLink,
  Edit2,
  RefreshCw
} from 'lucide-react';
import type { PrescriptionResponse, PrescriptionItem, MedicineProduct } from '../types';
import {
  addPrescriptionItem,
  updatePrescriptionItem,
  deletePrescriptionItem,
  getPrescriptionPdfUrl,
  getMedicineById
} from '../api';

interface PrescriptionStudioViewProps {
  prescription: PrescriptionResponse | null;
  onRefreshPrescription: () => void;
  onInspectEvidence: (candidate: MedicineProduct, queryText: string) => void;
  onNavigateToScan: () => void;
}

export const PrescriptionStudioView: FC<PrescriptionStudioViewProps> = ({
  prescription,
  onRefreshPrescription,
  onInspectEvidence,
  onNavigateToScan
}) => {
  const [newItemText, setNewItemText] = useState<string>('');
  const [newRefPrice, setNewRefPrice] = useState<string>('');
  const [addingItem, setAddingItem] = useState<boolean>(false);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState<string>('');
  const [editCandidateId, setEditCandidateId] = useState<string>('');

  const handleAddItem = async (e: FormEvent) => {
    e.preventDefault();
    if (!prescription || !newItemText.trim()) return;

    setAddingItem(true);
    try {
      const priceVal = parseFloat(newRefPrice);
      await addPrescriptionItem(prescription.prescription_id, {
        original_text: newItemText.trim(),
        prescribed_name: newItemText.trim(),
        user_reference_price_inr: !isNaN(priceVal) && priceVal > 0 ? priceVal : undefined
      });
      setNewItemText('');
      setNewRefPrice('');
      onRefreshPrescription();
    } catch (err) {
      console.error('Failed to add prescription item:', err);
    } finally {
      setAddingItem(false);
    }
  };

  const handleUpdateItem = async (itemId: string) => {
    if (!prescription) return;
    try {
      const pVal = parseFloat(editPrice);
      await updatePrescriptionItem(prescription.prescription_id, itemId, {
        user_reference_price_inr: !isNaN(pVal) && pVal > 0 ? pVal : undefined,
        selected_candidate_id: editCandidateId.trim() || undefined
      });
      setEditingItemId(null);
      setEditPrice('');
      setEditCandidateId('');
      onRefreshPrescription();
    } catch (err) {
      console.error('Failed to update prescription item:', err);
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!prescription) return;
    try {
      await deletePrescriptionItem(prescription.prescription_id, itemId);
      onRefreshPrescription();
    } catch (err) {
      console.error('Failed to delete item:', err);
    }
  };

  const handleInspect = async (item: PrescriptionItem) => {
    if (!item.candidate_id) return;
    try {
      const prod = await getMedicineById(item.candidate_id);
      onInspectEvidence(prod, item.prescribed_name);
    } catch (err) {
      console.error('Failed to fetch candidate details:', err);
    }
  };

  const handleDownloadPdf = () => {
    if (!prescription) return;
    const url = getPrescriptionPdfUrl(prescription.prescription_id);
    window.open(url, '_blank');
  };

  const summary = prescription?.summary;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f766e', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
            <FileText className="w-4 h-4" />
            <span>Prescription Savings Studio</span>
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Whole-Prescription Comparison & Pharmacist Audit
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            ID: {prescription?.prescription_id || 'Connecting...'} • Item-level evidence checks and quarantined unresolved totals.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onNavigateToScan}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '0.55rem 0.9rem',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem'
            }}
          >
            <span>Scan Packaging</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="search-button"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 1.1rem', fontSize: '0.85rem' }}
          >
            <Download className="w-4 h-4" />
            <span>Download Pharmacist PDF Report</span>
          </button>
        </div>
      </div>

      {/* 3 Distinct Totals Cards */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1.75rem' }}>
          {/* Total A: Confirmed Potential Savings */}
          <div style={{ background: 'linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%)', border: '1px solid #99f6e4', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
              <ShieldCheck className="w-4 h-4" />
              <span>Confirmed Potential Savings</span>
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#065f46', marginBottom: '0.2rem' }}>
              ₹{summary.confirmed_total_savings_inr.toFixed(2)}
              <span style={{ fontSize: '0.95rem', fontWeight: 700, marginLeft: '0.4rem', color: '#0d9488' }}>
                ({summary.confirmed_savings_percentage}%)
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#134e4a' }}>
              Applies to <b>{summary.verified_comparisons_count}</b> verified items with confirmed reference price evidence.
            </div>
          </div>

          {/* Total B: Unresolved Items Count */}
          <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#92400e', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
              <AlertTriangle className="w-4 h-4" />
              <span>Unresolved Items (Quarantined)</span>
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#78350f', marginBottom: '0.2rem' }}>
              {summary.unresolved_items_count} <span style={{ fontSize: '1rem', fontWeight: 600 }}>of {summary.total_items_count} items</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#92400e' }}>
              Excluded from confirmed total due to missing strengths, combination conflicts, or unlisted catalogue prices.
            </div>
          </div>

          {/* Total C: Excluded Potential Savings Estimate */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
              <Info className="w-4 h-4" />
              <span>Excluded Informational Estimate</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
              {summary.excluded_potential_savings_inr !== null && summary.excluded_potential_savings_inr !== undefined ? `₹${summary.excluded_potential_savings_inr.toFixed(2)}` : 'Cannot estimate'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Informational projection only. Strictly EXCLUDED from confirmed total until clinical attributes are confirmed.
            </div>
          </div>
        </div>
      )}

      {/* Add New Line Item Form */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.5rem' }}>
        <form onSubmit={handleAddItem} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 2, minWidth: '240px' }}>
            <input
              type="text"
              placeholder="Enter medicine name & strength (e.g., 'Atorvastatin 10mg', 'Metformin 500')..."
              value={newItemText}
              onChange={(e) => setNewItemText(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-app)',
                color: 'var(--text-primary)',
                fontSize: '0.88rem'
              }}
            />
          </div>
          <div style={{ flex: 1, minWidth: '150px' }}>
            <input
              type="number"
              step="0.01"
              placeholder="Reference MRP (₹, optional)"
              value={newRefPrice}
              onChange={(e) => setNewRefPrice(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-app)',
                color: 'var(--text-primary)',
                fontSize: '0.88rem'
              }}
            />
          </div>
          <button
            type="submit"
            disabled={addingItem || !newItemText.trim()}
            className="search-button"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.65rem 1.1rem', fontSize: '0.85rem' }}
          >
            <Plus className="w-4 h-4" />
            <span>Add Item</span>
          </button>
        </form>
      </div>

      {/* Itemized Prescription Table */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', marginBottom: '2rem' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Prescription Line Items ({prescription?.items.length || 0})
          </h3>
          <button
            type="button"
            onClick={onRefreshPrescription}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem' }}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Re-verify All</span>
          </button>
        </div>

        {(!prescription || prescription.items.length === 0) ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
            <FileText className="w-10 h-10 text-slate-300" style={{ margin: '0 auto 0.75rem auto' }} />
            <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
              No prescription items added yet
            </div>
            <div style={{ fontSize: '0.85rem' }}>
              Add medicine names above, or scan a packaging strip to populate verified generic matches.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-app)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Prescribed Medicine</th>
                  <th style={{ padding: '0.75rem 1rem' }}>PMBJP Generic Match</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Verification State</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Reference MRP</th>
                  <th style={{ padding: '0.75rem 1rem' }}>PMBJP MRP</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Confirmed Saving</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {prescription.items.map((item) => {
                  const isVerified = (item.verification_status === 'VERIFIED_FOR_PRICE_COMPARISON' && item.is_eligible_for_savings);
                  const isEditing = editingItemId === item.item_id;

                  return (
                    <tr key={item.item_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      {/* Prescribed Item */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{item.prescribed_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.original_text}</div>
                      </td>

                      {/* Generic Match */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {item.candidate_name ? (
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{item.candidate_name}</div>
                            <div style={{ fontSize: '0.72rem', color: '#0f766e' }}>
                              {item.candidate_id} • {item.candidate_unit_size}
                            </div>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No candidate linked</span>
                        )}
                      </td>

                      {/* Status */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {isVerified ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: '#065f46', background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-full)', fontSize: '0.72rem', fontWeight: 700 }}>
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Verified</span>
                          </span>
                        ) : (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: '#92400e', background: '#fffbeb', border: '1px solid #fde68a', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-full)', fontSize: '0.72rem', fontWeight: 700 }}>
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Clarification</span>
                          </span>
                        )}
                      </td>

                      {/* Reference Price */}
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>
                        {isEditing ? (
                          <input
                            type="number"
                            step="0.01"
                            value={editPrice}
                            placeholder="Price (₹)"
                            onChange={(e) => setEditPrice(e.target.value)}
                            style={{ width: '80px', padding: '0.2rem 0.4rem', fontSize: '0.8rem', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}
                          />
                        ) : (
                          item.reference_price_inr !== null && item.reference_price_inr !== undefined ? `₹${item.reference_price_inr.toFixed(2)}` : (item.user_reference_price_inr ? `₹${item.user_reference_price_inr.toFixed(2)}` : '—')
                        )}
                      </td>

                      {/* Comparison Price */}
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>
                        {item.comparison_price_inr !== null && item.comparison_price_inr !== undefined ? `₹${item.comparison_price_inr.toFixed(2)}` : (item.candidate_mrp_inr ? `₹${item.candidate_mrp_inr.toFixed(2)}` : '—')}
                      </td>

                      {/* Saving */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {isVerified && item.calculated_saving_inr !== null && item.calculated_saving_inr !== undefined ? (
                          <span style={{ color: '#059669', fontWeight: 800 }}>
                            +₹{item.calculated_saving_inr.toFixed(2)}
                          </span>
                        ) : (
                          <span style={{ color: '#b45309', fontSize: '0.75rem', fontWeight: 600 }}>
                            Quarantined
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end', alignItems: 'center' }}>
                          {isEditing ? (
                            <button
                              type="button"
                              onClick={() => handleUpdateItem(item.item_id)}
                              style={{ background: '#0f766e', color: '#ffffff', border: 'none', borderRadius: '4px', padding: '0.25rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer' }}
                            >
                              Save
                            </button>
                          ) : (
                            <button
                              type="button"
                              title="Clarify strength or price"
                              onClick={() => {
                                setEditingItemId(item.item_id);
                                setEditPrice(item.user_reference_price_inr ? item.user_reference_price_inr.toString() : '');
                                setEditCandidateId(item.candidate_id || '');
                              }}
                              style={{ background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '0.25rem 0.4rem', cursor: 'pointer', color: 'var(--text-muted)' }}
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                          )}

                          {item.candidate_id && (
                            <button
                              type="button"
                              title="Inspect Clinical Evidence"
                              onClick={() => handleInspect(item)}
                              style={{ background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '0.25rem 0.4rem', cursor: 'pointer', color: '#0f766e' }}
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </button>
                          )}

                          <button
                            type="button"
                            title="Remove Line Item"
                            onClick={() => handleDeleteItem(item.item_id)}
                            style={{ background: 'none', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '0.25rem 0.4rem', cursor: 'pointer', color: '#dc2626' }}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Mandatory Pharmacist & Clinical Notice */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 'var(--radius-lg)', padding: '1rem', fontSize: '0.78rem', color: '#475569', lineHeight: '1.4' }}>
        <b>Notice for Pharmacists and Prescribers:</b> MedWise price difference assessments are calculated deterministically against official Jan Aushadhi (PMBJP) pricing schedules and NPPA DPCO statutory price caps. Unresolved items (missing strengths, combination drugs, or unlisted prices) are strictly quarantined from confirmed savings to guarantee transparency. Generic substitutions must always be evaluated and approved by a licensed medical practitioner or registered pharmacist.
      </div>
    </div>
  );
};

import type { FC } from 'react';
import { ShoppingBag, Trash2, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import type { BasketItem } from '../types';

interface BasketViewProps {
  basket: BasketItem[];
  onRemoveItem: (id: string) => void;
  onClearBasket: () => void;
  onInspectEvidence: (item: BasketItem) => void;
}

export const BasketView: FC<BasketViewProps> = ({
  basket,
  onRemoveItem,
  onClearBasket,
  onInspectEvidence
}) => {
  if (basket.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', background: '#ffffff', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
        <ShoppingBag className="w-12 h-12 text-slate-300" style={{ margin: '0 auto 1rem auto' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Your Prescription Basket is Empty
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto' }}>
          Search for prescribed medicines or generic alternatives, inspect the match evidence, and add verified comparisons to track potential cumulative savings.
        </p>
      </div>
    );
  }

  // Split into confirmed vs unresolved
  const confirmedItems = basket.filter(
    (item) => item.verification.verification_status === 'VERIFIED_FOR_PRICE_COMPARISON' && item.verification.savings.is_eligible
  );

  const unresolvedItems = basket.filter(
    (item) => item.verification.verification_status !== 'VERIFIED_FOR_PRICE_COMPARISON' || !item.verification.savings.is_eligible
  );

  const totalConfirmedSaving = confirmedItems.reduce(
    (acc, item) => acc + (item.verification.savings.absolute_saving_inr || 0),
    0
  );

  const totalReferenceSpend = confirmedItems.reduce(
    (acc, item) => acc + (item.verification.savings.reference_price_inr || 0),
    0
  );

  const totalGenericSpend = confirmedItems.reduce(
    (acc, item) => acc + (item.verification.savings.comparison_price_inr || 0),
    0
  );

  const overallPercentage = totalReferenceSpend > 0 ? ((totalConfirmedSaving / totalReferenceSpend) * 100).toFixed(1) : '0';

  return (
    <div>
      {/* Basket Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f2744' }}>Prescription Basket</h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            Transparent itemized tally of verified comparisons and unconfirmed items.
          </p>
        </div>
        <button
          onClick={onClearBasket}
          style={{
            background: 'none',
            border: '1px solid var(--border-subtle)',
            padding: '0.4rem 0.8rem',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-muted)',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem'
          }}
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Basket</span>
        </button>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {/* Confirmed Cumulative Savings */}
        <div style={{ background: 'linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%)', border: '1px solid #99f6e4', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f766e', fontWeight: 700, fontSize: '0.82rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            <ShieldCheck className="w-4 h-4" />
            <span>Confirmed Potential Savings</span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#065f46' }}>
            ₹{totalConfirmedSaving.toFixed(2)}
            <span style={{ fontSize: '1rem', fontWeight: 700, marginLeft: '0.4rem', color: '#0d9488' }}>
              ({overallPercentage}%)
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#0f766e', marginTop: '0.5rem' }}>
            Calculated across {confirmedItems.length} verified item(s). Excludes unconfirmed/incompatible items.
          </div>
        </div>

        {/* Spend Comparison */}
        <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Spend Breakdown (Standardized Units)
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Reference Brand MRP:</span>
            <span style={{ fontWeight: 700, color: '#0f2744' }}>₹{totalReferenceSpend.toFixed(2)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Jan Aushadhi Generic MRP:</span>
            <span style={{ fontWeight: 700, color: '#0f766e' }}>₹{totalGenericSpend.toFixed(2)}</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>
            All prices normalized to identical pack unit quantities before summing.
          </div>
        </div>
      </div>

      {/* Confirmed Items List */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f2744', marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <span>Verified Comparisons ({confirmedItems.length})</span>
        </h3>
        {confirmedItems.length === 0 ? (
          <div style={{ background: '#ffffff', padding: '1rem', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)', fontSize: '0.85rem', border: '1px solid var(--border-subtle)' }}>
            No comparisons verified yet. Items requiring strength or form clarification are listed below.
          </div>
        ) : (
          confirmedItems.map((item) => (
            <div key={item.id} className="basket-item">
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                    {item.candidate.name}
                  </span>
                  <span style={{ fontSize: '0.7rem', fontWeight: 600, background: '#ecfdf5', color: '#059669', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)' }}>
                    VERIFIED
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Prescribed search: "{item.query}" • Pack: {item.candidate.unit_size} • ID: {item.candidate.product_id}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#0f766e', marginTop: '0.25rem', fontFamily: 'var(--font-mono)' }}>
                  Difference: ₹{item.verification.savings.absolute_saving_inr} ({item.verification.savings.percentage_saving}%) on {item.verification.savings.normalized_unit_basis}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <button
                  onClick={() => onInspectEvidence(item)}
                  style={{
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-subtle)',
                    padding: '0.4rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Evidence
                </button>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#e11d48',
                    cursor: 'pointer',
                    padding: '0.4rem'
                  }}
                  title="Remove item"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Unresolved / Ineligible Items List */}
      {unresolvedItems.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#92400e', marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span>Unresolved / Excluded from Confirmed Savings ({unresolvedItems.length})</span>
          </h3>
          <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)', padding: '0.75rem 1rem', marginBottom: '0.85rem', fontSize: '0.8rem', color: '#92400e' }}>
            <strong>Rule D Compliance:</strong> These medicines are retained for your reference, but excluded from total savings because strength, form, or price evidence is unverified or incompatible.
          </div>
          {unresolvedItems.map((item) => (
            <div key={item.id} className="basket-item" style={{ borderLeft: '4px solid #d97706' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                    {item.candidate.name}
                  </span>
                  <span style={{ fontSize: '0.7rem', fontWeight: 600, background: '#fffbeb', color: '#d97706', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)' }}>
                    {item.verification.verification_status}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Prescribed search: "{item.query}" • {item.candidate.unit_size}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#b45309', marginTop: '0.25rem' }}>
                  Reason: {item.verification.savings.ineligible_reason || item.verification.plain_language_summary}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <button
                  onClick={() => onInspectEvidence(item)}
                  style={{
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-subtle)',
                    padding: '0.4rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Clarify
                </button>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#e11d48',
                    cursor: 'pointer',
                    padding: '0.4rem'
                  }}
                  title="Remove item"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

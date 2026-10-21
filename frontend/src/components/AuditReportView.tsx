import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { FileCheck } from 'lucide-react';
import { fetchDataQualityReport } from '../api';

export const AuditReportView: FC = () => {
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDataQualityReport()
      .then((data) => setReportData(data))
      .catch((err) => setError(err.message || 'Failed to load report'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f2744' }}>
          Phase 2 Data Quality & Provenance Audit
        </h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
          Transparent documentation of source datasets, cleaning criteria, zero-MRP exclusions, and statutory ceiling price boundaries.
        </p>
      </div>

      {loading && <div style={{ color: 'var(--text-muted)' }}>Loading official audit report...</div>}
      {error && <div style={{ color: '#e11d48' }}>{error}</div>}

      {reportData && (
        <>
          {/* Key Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Generic Medicines</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0f2744' }}>{reportData.stats?.generic_count || 2439}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total rows from Jan Aushadhi (PMBJP)</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Verified Usable Prices</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#059669' }}>{reportData.stats?.generic_usable_price_count || 2095}</div>
              <div style={{ fontSize: '0.75rem', color: '#059669' }}>Positive MRP verified for comparison</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Zero/Invalid Prices Flagged</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#d97706' }}>
                {(reportData.stats?.generic_count || 2439) - (reportData.stats?.generic_usable_price_count || 2095)}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#d97706' }}>Strictly excluded from savings engine</div>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Statutory Ceiling Prices</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0284c7' }}>{reportData.stats?.ceiling_count || 915}</div>
              <div style={{ fontSize: '0.75rem', color: '#0284c7' }}>NPPA / DPCO 2013 Reference caps</div>
            </div>
          </div>

          {/* Full Audit Report Text */}
          <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
              <FileCheck className="w-5 h-5 text-teal-600" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f2744' }}>
                Original Cleaned Audit Log (data_quality_report.txt)
              </h3>
            </div>
            <pre
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                lineHeight: 1.6,
                color: 'var(--text-secondary)',
                whiteSpace: 'pre-wrap',
                background: 'var(--bg-canvas)',
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                overflowX: 'auto'
              }}
            >
              {reportData.content}
            </pre>
          </div>
        </>
      )}
    </div>
  );
};

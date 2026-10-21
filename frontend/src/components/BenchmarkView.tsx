import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { Cpu, Play, CheckCircle2, XCircle, Clock, RefreshCw } from 'lucide-react';
import type { BenchmarkReport } from '../types';
import { runComparativeBenchmark, fetchAiStatus } from '../api';

export const BenchmarkView: FC = () => {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<any>(null);

  const loadBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runComparativeBenchmark();
      setReport(data);
      const ai = await fetchAiStatus();
      setAiStatus(ai);
    } catch (err: any) {
      setError(err.message || 'Failed to run comparative benchmark');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBenchmark();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f2744' }}>
            3-Mode Comparative Search Benchmark
          </h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            Empirical evaluation comparing Exact Matching, Fuzzy+Deterministic, and Gemma-Assisted retrieval on identical clinical & adversarial queries.
          </p>
        </div>
        <button
          onClick={loadBenchmark}
          disabled={loading}
          style={{
            background: '#0d9488',
            color: 'white',
            border: 'none',
            padding: '0.55rem 1.1rem',
            borderRadius: 'var(--radius-md)',
            fontWeight: 700,
            fontSize: '0.88rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          <span>{loading ? 'Evaluating...' : 'Re-run Benchmark'}</span>
        </button>
      </div>

      {/* Ollama & Model Status Card */}
      {aiStatus && (
        <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Cpu className="w-5 h-5 text-teal-600" />
              <span style={{ fontWeight: 800, fontSize: '0.95rem', color: '#0f2744' }}>
                Local Gemma Runtime (Ollama Engine)
              </span>
            </div>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.2rem 0.6rem',
                borderRadius: 'var(--radius-full)',
                background: aiStatus.ollama_online ? '#ecfdf5' : '#fff1f2',
                color: aiStatus.ollama_online ? '#059669' : '#e11d48',
                border: `1px solid ${aiStatus.ollama_online ? '#a7f3d0' : '#fecdd3'}`
              }}
            >
              {aiStatus.ollama_online ? 'OLLAMA ONLINE' : 'LOCAL AI OFFLINE (SAFE FALLBACK ACTIVE)'}
            </span>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            {aiStatus.status_message}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Target Model: <code>{aiStatus.target_model}</code> • Rule D Policy: When offline, the deterministic engine executes without simulating AI responses.
          </div>
        </div>
      )}

      {error && (
        <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#9f1239', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {report && (
        <>
          {/* Comparative Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            {/* Mode A: Exact */}
            <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Mode A: Exact String Match</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f2744', marginTop: '0.35rem' }}>
                {report.mode_a_exact.top1_accuracy}%
                <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '0.4rem' }}>Top-1 Accuracy</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Top-3 Recall: <strong>{report.mode_a_exact.top3_recall}%</strong>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Abstention Rate: <strong>{report.mode_a_exact.correct_abstention_rate}%</strong>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock className="w-3.5 h-3.5" />
                <span>Avg Latency: {report.mode_a_exact.avg_latency_ms} ms</span>
              </div>
            </div>

            {/* Mode B: Fuzzy + Deterministic */}
            <div style={{ background: 'linear-gradient(135deg, #f0fdfa 0%, #ffffff 100%)', border: '2px solid #0d9488', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0d9488', textTransform: 'uppercase' }}>Mode B: Fuzzy + Deterministic</span>
                <span style={{ fontSize: '0.68rem', fontWeight: 700, background: '#0d9488', color: 'white', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)' }}>RECOMMENDED</span>
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f766e', marginTop: '0.35rem' }}>
                {report.mode_b_fuzzy_deterministic.top1_accuracy}%
                <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '0.4rem' }}>Top-1 Accuracy</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Top-3 Recall: <strong>{report.mode_b_fuzzy_deterministic.top3_recall}%</strong>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Abstention Rate: <strong>{report.mode_b_fuzzy_deterministic.correct_abstention_rate}%</strong>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock className="w-3.5 h-3.5" />
                <span>Avg Latency: {report.mode_b_fuzzy_deterministic.avg_latency_ms} ms</span>
              </div>
            </div>

            {/* Mode C: Gemma Assisted */}
            <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0284c7', textTransform: 'uppercase' }}>Mode C: Gemma-Assisted + Pipeline</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0369a1', marginTop: '0.35rem' }}>
                {report.mode_c_gemma_assisted.top1_accuracy}%
                <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '0.4rem' }}>Top-1 Accuracy</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Top-3 Recall: <strong>{report.mode_c_gemma_assisted.top3_recall}%</strong>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Abstention Rate: <strong>{report.mode_c_gemma_assisted.correct_abstention_rate}%</strong>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock className="w-3.5 h-3.5" />
                <span>Avg Latency: {report.mode_c_gemma_assisted.avg_latency_ms} ms</span>
              </div>
            </div>
          </div>

          {/* Test Cases Table */}
          <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', overflowX: 'auto' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f2744', marginBottom: '0.75rem' }}>
              Individual Query Case Evaluation ({report.total_test_cases} Queries)
            </h3>
            <table className="benchmark-table">
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Mode A (Exact)</th>
                  <th>Mode B (Fuzzy)</th>
                  <th>Mode C (Gemma)</th>
                </tr>
              </thead>
              <tbody>
                {report.detailed_results.map((row, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>"{row.case.query}"</td>
                    <td>
                      <span style={{ fontSize: '0.72rem', background: 'var(--bg-canvas)', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                        {row.case.category}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{row.case.description}</td>
                    <td>
                      {row.mode_a_hit ? (
                        <span style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '0.2rem', fontWeight: 600 }}>
                          <CheckCircle2 className="w-4 h-4" /> Pass
                        </span>
                      ) : (
                        <span style={{ color: '#e11d48', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <XCircle className="w-4 h-4" /> Fail
                        </span>
                      )}
                    </td>
                    <td>
                      {row.mode_b_hit ? (
                        <span style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '0.2rem', fontWeight: 600 }}>
                          <CheckCircle2 className="w-4 h-4" /> Pass
                        </span>
                      ) : (
                        <span style={{ color: '#e11d48', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <XCircle className="w-4 h-4" /> Fail
                        </span>
                      )}
                    </td>
                    <td>
                      {row.mode_c_hit ? (
                        <span style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '0.2rem', fontWeight: 600 }}>
                          <CheckCircle2 className="w-4 h-4" /> Pass
                        </span>
                      ) : (
                        <span style={{ color: '#e11d48', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                          <XCircle className="w-4 h-4" /> Fail
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

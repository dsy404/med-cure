import { useState, useEffect } from 'react';
import {
  Search,
  ShieldCheck,
  BarChart2,
  FileCheck,
  BookOpen,
  Sparkles,
  Activity,
  Sun,
  Moon,
  Filter,
  Info,
  Camera,
  MapPin,
  Share2,
  FileText
} from 'lucide-react';

import type {
  SearchResponse,
  MedicineProduct,
  VerificationResult,
  GemmaInterpretation,
  PrescriptionResponse
} from './types';
import {
  fetchHealth,
  searchMedicines,
  verifyCandidate,
  interpretWithAi,
  createPrescription,
  getPrescription,
  addPrescriptionItem
} from './api';

import { EvidenceCard } from './components/EvidenceCard';
import { PrescriptionStudioView } from './components/PrescriptionStudioView';
import { ScanPackagingView } from './components/ScanPackagingView';
import { KendraFinderView } from './components/KendraFinderView';
import { EvidenceExplorerView } from './components/EvidenceExplorerView';
import { BenchmarkView } from './components/BenchmarkView';
import { AuditReportView } from './components/AuditReportView';
import { MethodologyView } from './components/MethodologyView';

type TabType =
  | 'search'
  | 'scan'
  | 'prescription'
  | 'kendra'
  | 'evidence'
  | 'benchmark'
  | 'methodology'
  | 'audit';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('search');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Search state
  const [query, setQuery] = useState<string>('');
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [includeCeiling, setIncludeCeiling] = useState<boolean>(true);
  const [searchMode, setSearchMode] = useState<'deterministic' | 'ai'>('deterministic');
  const [aiInterpretation, setAiInterpretation] = useState<GemmaInterpretation | null>(null);
  const [candidateFilter, setCandidateFilter] = useState<'all' | 'single' | 'combination' | 'usable'>('all');

  // Evidence card modal state
  const [selectedCandidate, setSelectedCandidate] = useState<MedicineProduct | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [activeEvidenceDecisionId, setActiveEvidenceDecisionId] = useState<string | null>(null);

  // Prescription state
  const [prescription, setPrescription] = useState<PrescriptionResponse | null>(null);

  // Health state
  const [healthData, setHealthData] = useState<any>(null);

  // Initial health check and prescription initialization
  useEffect(() => {
    fetchHealth()
      .then((data) => setHealthData(data))
      .catch((err) => console.warn('Backend health check error:', err));

    const storedRxId = localStorage.getItem('medwise_prescription_id') || localStorage.getItem('medledger_prescription_id');
    if (storedRxId) {
      getPrescription(storedRxId)
        .then((rx) => setPrescription(rx))
        .catch(() => {
          // If stored id expired or invalid, create new
          createPrescription('My Prescription').then((newRx) => {
            setPrescription(newRx);
            localStorage.setItem('medwise_prescription_id', newRx.prescription_id);
          });
        });
    } else {
      createPrescription('My Prescription').then((newRx) => {
        setPrescription(newRx);
        localStorage.setItem('medwise_prescription_id', newRx.prescription_id);
      });
    }
  }, []);

  const refreshPrescription = () => {
    if (!prescription) return;
    getPrescription(prescription.prescription_id)
      .then((rx) => setPrescription(rx))
      .catch((err) => console.warn('Failed to refresh prescription:', err));
  };

  // Handle Search Submission
  const handleSearch = async (overrideQuery?: string) => {
    const q = (overrideQuery !== undefined ? overrideQuery : query).trim();
    if (!q) return;

    setLoading(true);
    setSearchError(null);
    setAiInterpretation(null);

    try {
      let activeQuery = q;

      if (searchMode === 'ai') {
        try {
          const aiRes = await interpretWithAi(q);
          setAiInterpretation(aiRes);
          if (aiRes.interpreted_name) {
            activeQuery = aiRes.interpreted_name;
          }
        } catch (aiErr) {
          console.warn('AI interpretation skipped; falling back to deterministic:', aiErr);
        }
      }

      const res = await searchMedicines(activeQuery, 12, includeCeiling);
      setSearchResponse(res);
    } catch (err: any) {
      setSearchError(err.message || 'Error occurred while querying catalogue.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickChip = (chipText: string) => {
    setQuery(chipText);
    handleSearch(chipText);
  };

  // Handle candidate selection for verification modal
  const handleVerifyCandidate = async (candidate: MedicineProduct, customQuery?: string) => {
    setSelectedCandidate(candidate);
    const q = (customQuery || query || candidate.name).trim();
    try {
      const vRes = await verifyCandidate(q, candidate.product_id);
      setVerificationResult(vRes);
      if (vRes.decision_id) {
        setActiveEvidenceDecisionId(vRes.decision_id);
      }
    } catch (err) {
      console.error('Verification call failed:', err);
    }
  };

  // Add item to prescription
  const handleAddToPrescription = async (candidate: MedicineProduct, verification: VerificationResult) => {
    if (!prescription) return;
    try {
      await addPrescriptionItem(prescription.prescription_id, {
        original_text: verification.query,
        prescribed_name: verification.query,
        selected_candidate_id: candidate.product_id,
        user_reference_price_inr: verification.savings.reference_price_inr || undefined
      });
      refreshPrescription();
    } catch (err) {
      console.error('Failed to add to prescription:', err);
    }
  };

  const handleAddFromScan = async (text: string, candidateId?: string) => {
    if (!prescription || !text.trim()) return;
    try {
      await addPrescriptionItem(prescription.prescription_id, {
        original_text: text.trim(),
        prescribed_name: text.trim(),
        selected_candidate_id: candidateId
      });
      refreshPrescription();
      setActiveTab('prescription');
    } catch (err) {
      console.error('Failed to add scan item:', err);
    }
  };

  const handleOpenEvidenceGraph = (decisionId: string) => {
    setActiveEvidenceDecisionId(decisionId);
    setActiveTab('evidence');
  };

  // Skeleton loading cards
  const renderSkeletonCards = () => (
    <div className="candidate-grid">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="candidate-card" style={{ padding: '1.5rem' }}>
          <div>
            <div className="skeleton skeleton-line long" style={{ height: '18px', marginBottom: '12px' }} />
            <div className="skeleton skeleton-line medium" style={{ height: '12px', marginBottom: '16px' }} />
            <div style={{ display: 'flex', gap: '6px', marginBottom: '16px' }}>
              <div className="skeleton" style={{ width: '80px', height: '24px', borderRadius: 'var(--radius-sm)' }} />
              <div className="skeleton" style={{ width: '50px', height: '24px', borderRadius: 'var(--radius-sm)' }} />
              <div className="skeleton" style={{ width: '65px', height: '24px', borderRadius: 'var(--radius-sm)' }} />
            </div>
            <div className="skeleton" style={{ height: '56px', borderRadius: 'var(--radius-md)', marginBottom: '12px' }} />
            <div className="skeleton" style={{ height: '40px', borderRadius: 'var(--radius-md)' }} />
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="app-container">
      {/* Header Bar */}
      <header className="header-bar">
        <div className="header-inner">
          <div className="brand-wrapper" onClick={() => setActiveTab('search')}>
            <div className="brand-icon">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="brand-title">
                MedWise
                <span className="brand-badge">India Edition</span>
              </div>
            </div>
          </div>

          {/* Navigation Buttons */}
          <nav className="nav-links">
            <button
              className={`nav-button ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <Search className="w-4 h-4" />
              <span>Search & Verify</span>
            </button>

            <button
              className={`nav-button ${activeTab === 'scan' ? 'active' : ''}`}
              onClick={() => setActiveTab('scan')}
            >
              <Camera className="w-4 h-4" />
              <span>Scan Packaging</span>
            </button>

            <button
              className={`nav-button ${activeTab === 'prescription' ? 'active' : ''}`}
              onClick={() => setActiveTab('prescription')}
            >
              <FileText className="w-4 h-4" />
              <span>Prescription Studio</span>
              {prescription && prescription.items.length > 0 && (
                <span style={{ background: 'var(--accent)', color: 'var(--text-inverse)', fontSize: '0.65rem', padding: '0.1rem 0.45rem', borderRadius: 'var(--radius-full)', fontWeight: 700 }}>
                  {prescription.items.length}
                </span>
              )}
            </button>

            <button
              className={`nav-button ${activeTab === 'kendra' ? 'active' : ''}`}
              onClick={() => setActiveTab('kendra')}
            >
              <MapPin className="w-4 h-4" />
              <span>Kendra Finder</span>
            </button>

            <button
              className={`nav-button ${activeTab === 'evidence' ? 'active' : ''}`}
              onClick={() => setActiveTab('evidence')}
            >
              <Share2 className="w-4 h-4" />
              <span>Evidence Graph</span>
            </button>

            <button
              className={`nav-button ${activeTab === 'benchmark' ? 'active' : ''}`}
              onClick={() => setActiveTab('benchmark')}
            >
              <BarChart2 className="w-4 h-4" />
              <span>3-Mode Benchmark</span>
            </button>

            <button
              className={`nav-button ${activeTab === 'methodology' ? 'active' : ''}`}
              onClick={() => setActiveTab('methodology')}
            >
              <BookOpen className="w-4 h-4" />
              <span>Methodology</span>
            </button>

            <button
              className={`nav-button ${activeTab === 'audit' ? 'active' : ''}`}
              onClick={() => setActiveTab('audit')}
            >
              <FileCheck className="w-4 h-4" />
              <span>Data Audit</span>
            </button>
          </nav>

          {/* Header Controls: Health Pill + Theme Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div className="health-pill">
              <span className="health-dot"></span>
              <span>
                {healthData?.datasets?.loaded
                  ? `${healthData.datasets.generic_products_total} Generics • ${healthData.datasets.ceiling_price_references} DPCO`
                  : 'Connecting...'}
              </span>
            </div>

            <button
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} theme`}
              aria-label="Toggle theme"
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '0.45rem',
                cursor: 'pointer',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'var(--shadow-xs)',
                transition: 'all 0.2s'
              }}
            >
              {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4 text-amber-400" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'search' && (
          <div>
            {/* Hero Section */}
            <section className="hero-section">
              <div className="hero-tag">
                <Activity className="w-4 h-4" />
                <span>Every medicine match. Every price. Every claim backed by evidence.</span>
              </div>
              <h1 className="hero-headline">
                Evidence-First Medicine <span className="gradient-text">Price Intelligence</span>
              </h1>
              <p className="hero-subtext">
                Search generic and prescribed medicines, trace verified PMBJP Jan Aushadhi catalogues and NPPA DPCO ceiling price caps, and compute deterministic, clinical evidence-backed savings.
              </p>

              {/* Search Card Container */}
              <div className="search-card">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSearch();
                  }}
                >
                  <div className="search-input-wrapper">
                    <Search className="w-5 h-5" style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    <input
                      type="text"
                      className="search-input"
                      placeholder="Enter brand name, generic molecule, or dosage (e.g., 'Dolo 650', 'Atorvastatin 10mg')..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                    <button type="submit" className="search-button" disabled={loading}>
                      {loading ? 'Searching...' : 'Search'}
                    </button>
                  </div>
                </form>

                {/* Quick Query Suggestion Chips */}
                <div className="chips-container">
                  <span className="chips-label">Popular Searches:</span>
                  {[
                    'Dolo 650',
                    'Augmentin 625',
                    'Atorvastatin 10mg',
                    'Metformin 500',
                    'Pantocid 40',
                    'Telma 40',
                    'Aspirin 300mg'
                  ].map((chip) => (
                    <button
                      key={chip}
                      className="chip-btn"
                      onClick={() => handleQuickChip(chip)}
                      type="button"
                    >
                      {chip}
                    </button>
                  ))}
                </div>

                {/* Search Options & Filters */}
                <div className="search-controls">
                  <div className="controls-group">
                    <label className="checkbox-label" title="Toggle DPCO 2013 statutory ceiling caps">
                      <input
                        type="checkbox"
                        checked={includeCeiling}
                        onChange={(e) => setIncludeCeiling(e.target.checked)}
                      />
                      <span>Include NPPA DPCO Ceiling Price Caps (Reference)</span>
                    </label>
                  </div>

                  <div className="controls-group">
                    <div className="mode-toggle">
                      <button
                        type="button"
                        className={`mode-btn ${searchMode === 'deterministic' ? 'active' : ''}`}
                        onClick={() => setSearchMode('deterministic')}
                        title="Strict deterministic parsing and multi-stage exact/fuzzy retrieval"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Deterministic Mode</span>
                      </button>
                      <button
                        type="button"
                        className={`mode-btn ${searchMode === 'ai' ? 'active' : ''}`}
                        onClick={() => setSearchMode('ai')}
                        title="Gemma model extracts dosage/form and assists noisy query interpretation"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>AI-Assisted (Gemma)</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* AI Interpretation Callout (If active) */}
                {aiInterpretation && (
                  <div className="ai-interpretation-box">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--violet)', fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                      <Sparkles className="w-4 h-4" />
                      <span>Local Gemma Interpretation ({aiInterpretation.model_name || 'gemma2:2b'})</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {aiInterpretation.reason}
                    </div>
                    {aiInterpretation.missing_attributes.length > 0 && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--status-amber)', marginTop: '0.35rem', fontWeight: 600 }}>
                        Missing attributes noted: {aiInterpretation.missing_attributes.join(', ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>

            {/* Error Message */}
            {searchError && (
              <div className="error-banner">
                <Info className="w-4 h-4" />
                <span>{searchError}</span>
              </div>
            )}

            {/* Skeleton Loading State */}
            {loading && renderSkeletonCards()}

            {/* Search Results Display */}
            {searchResponse && !loading && (
              <section className="results-section">
                {/* Results Header with Metadata */}
                <div className="results-header">
                  <div>
                    <h2 className="results-title">
                      Retrieved Catalogue Candidates ({searchResponse.total_candidates})
                    </h2>
                    <div className="results-meta">
                      Strategy Applied: <strong style={{ color: 'var(--accent)' }}>{searchResponse.retrieval_strategy_applied}</strong> • Query time: {searchResponse.execution_time_ms} ms
                    </div>
                  </div>

                  {/* Candidate Filters */}
                  {searchResponse.candidates.length > 0 && (
                    <div className="filter-pills">
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Filter className="w-3.5 h-3.5" /> Filter:
                      </span>
                      <button
                        className={`filter-pill ${candidateFilter === 'all' ? 'active' : ''}`}
                        onClick={() => setCandidateFilter('all')}
                      >
                        All ({searchResponse.candidates.length})
                      </button>
                      <button
                        className={`filter-pill ${candidateFilter === 'single' ? 'active' : ''}`}
                        onClick={() => setCandidateFilter('single')}
                      >
                        Single Molecule
                      </button>
                      <button
                        className={`filter-pill ${candidateFilter === 'combination' ? 'active' : ''}`}
                        onClick={() => setCandidateFilter('combination')}
                      >
                        Combination
                      </button>
                      <button
                        className={`filter-pill ${candidateFilter === 'usable' ? 'active' : ''}`}
                        onClick={() => setCandidateFilter('usable')}
                      >
                        Positive MRP Only
                      </button>
                    </div>
                  )}
                </div>

                {/* Filtered Candidate Cards Grid */}
                {(() => {
                  const filteredCandidates = searchResponse.candidates.filter((cand) => {
                    const prod = cand.product;
                    if (candidateFilter === 'single') return prod.attributes.ingredients.length === 1;
                    if (candidateFilter === 'combination') return prod.attributes.ingredients.length > 1;
                    if (candidateFilter === 'usable') return prod.price.usable_for_comparison && prod.price.amount_inr > 0;
                    return true;
                  });

                  if (filteredCandidates.length === 0) {
                    return (
                      <div className="no-candidates-card">
                        <Info className="w-10 h-10 text-slate-400" style={{ margin: '0 auto 0.75rem auto' }} />
                        <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                          No candidates match the selected filter
                        </div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                          Try selecting "All" or searching for a different generic salt name.
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div className="candidate-grid">
                      {filteredCandidates.map((cand) => {
                        const prod = cand.product;
                        const isCeiling = prod.catalogue_type === 'ceiling_price_reference';
                        const isSingleMolecule = prod.attributes.ingredients.length <= 1;

                        const getStrategyLabel = () => {
                          switch (cand.retrieval_method) {
                            case 'EXACT_MATCH': return 'Exact Match';
                            case 'ALIAS_MATCH': return 'Verified Brand Alias';
                            case 'NORMALIZED_MATCH': return 'Normalized Match';
                            case 'PARTIAL_MATCH': return 'Token Match';
                            case 'FUZZY_MATCH': return `Typo-Tolerant (${Math.round(cand.match_score)}%)`;
                            default: return cand.retrieval_method;
                          }
                        };

                        return (
                          <div key={prod.product_id} className="candidate-card">
                            <div>
                              <div className="card-top">
                                <div style={{ flex: 1, marginRight: '0.5rem' }}>
                                  <div className="product-name">{prod.name}</div>
                                  <div style={{ display: 'flex', gap: '0.35rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                                    {isSingleMolecule ? (
                                      <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.12rem 0.5rem', borderRadius: 'var(--radius-full)', background: 'var(--status-verified-bg)', color: 'var(--status-verified)', border: '1px solid var(--status-verified-border)' }}>
                                        Single Molecule
                                      </span>
                                    ) : (
                                      <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '0.12rem 0.5rem', borderRadius: 'var(--radius-full)', background: 'var(--status-amber-bg)', color: 'var(--status-amber)', border: '1px solid var(--status-amber-border)' }}>
                                        Combination Drug ({prod.attributes.ingredients.length} Molecules)
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <span className={`method-tag ${cand.retrieval_method.toLowerCase().replace('_match', '')}`} title="Candidate retrieval strategy applied">
                                  {getStrategyLabel()}
                                </span>
                              </div>

                              {cand.notes && (
                                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: '0.75rem', lineHeight: 1.45, background: 'rgba(148,163,184,0.05)', padding: '0.45rem 0.65rem', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--border-strong)' }}>
                                  {cand.notes}
                                </div>
                              )}

                              <div className="attribute-pills">
                                {prod.attributes.ingredients.map((ing, i) => (
                                  <span key={i} className="attr-pill" style={{ background: 'var(--accent-dim)', borderColor: 'var(--accent-border)', color: 'var(--accent)', fontWeight: 600 }}>
                                    {ing}
                                  </span>
                                ))}
                                {prod.attributes.strengths.map((str, s) => (
                                  <span key={s} className="attr-pill" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                    {str}
                                  </span>
                                ))}
                                {prod.attributes.dosage_form && (
                                  <span className="attr-pill">
                                    {prod.attributes.dosage_form}
                                  </span>
                                )}
                                <span className="attr-pill" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem' }}>
                                  ID: {prod.product_id}
                                </span>
                                <span className="attr-pill" style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                                  {isCeiling ? 'NPPA DPCO' : 'Jan Aushadhi PMBJP'}
                                </span>
                              </div>

                              <div className="price-box">
                                <div>
                                  <div className="price-value">
                                    ₹{prod.price.amount_inr}
                                    <span className="price-unit"> / {prod.unit_size}</span>
                                  </div>
                                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                                    {isCeiling ? 'NPPA DPCO Statutory Cap' : 'Jan Aushadhi PMBJP MRP'}
                                  </div>
                                </div>
                                <div>
                                  <span
                                    className="price-type-tag"
                                    style={{
                                      background: isCeiling ? 'var(--status-blue-bg)' : (prod.price.usable_for_comparison && prod.price.amount_inr > 0 ? 'var(--status-verified-bg)' : 'var(--status-rose-bg)'),
                                      color: isCeiling ? 'var(--status-blue)' : (prod.price.usable_for_comparison && prod.price.amount_inr > 0 ? 'var(--status-verified)' : 'var(--status-rose)'),
                                      border: `1px solid ${isCeiling ? 'var(--status-blue-border)' : (prod.price.usable_for_comparison && prod.price.amount_inr > 0 ? 'var(--status-verified-border)' : 'var(--status-rose-border)')}`
                                    }}
                                  >
                                    {isCeiling ? 'Statutory Cap' : (prod.price.usable_for_comparison && prod.price.amount_inr > 0 ? 'PMBJP Retail MRP' : 'Zero/Unlisted MRP')}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <button
                              className="verify-action-btn"
                              onClick={() => handleVerifyCandidate(prod)}
                            >
                              <ShieldCheck className="w-4 h-4" />
                              <span>Inspect Evidence & Compare</span>
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </section>
            )}

            {/* Evidence Card Modal */}
            {selectedCandidate && verificationResult && (
              <EvidenceCard
                result={verificationResult}
                candidateProduct={selectedCandidate}
                onClose={() => {
                  setSelectedCandidate(null);
                  setVerificationResult(null);
                }}
                onAddToBasket={handleAddToPrescription}
                onOpenEvidenceGraph={handleOpenEvidenceGraph}
              />
            )}
          </div>
        )}

        {activeTab === 'scan' && (
          <ScanPackagingView
            onSelectCandidateForVerification={handleVerifyCandidate}
            onAddPrescriptionItemFromScan={handleAddFromScan}
          />
        )}

        {activeTab === 'prescription' && (
          <PrescriptionStudioView
            prescription={prescription}
            onRefreshPrescription={refreshPrescription}
            onInspectEvidence={(cand, qText) => handleVerifyCandidate(cand, qText)}
            onNavigateToScan={() => setActiveTab('scan')}
          />
        )}

        {activeTab === 'kendra' && <KendraFinderView />}

        {activeTab === 'evidence' && (
          <EvidenceExplorerView initialDecisionId={activeEvidenceDecisionId} />
        )}

        {activeTab === 'benchmark' && <BenchmarkView />}

        {activeTab === 'audit' && <AuditReportView />}

        {activeTab === 'methodology' && <MethodologyView />}
      </main>

      {/* Footer Bar */}
      <footer className="footer-bar">
        <div className="footer-inner">
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>MedWise</strong> — Every medicine match. Every price. Every claim backed by evidence.
          </div>
          <div style={{ fontSize: '0.78rem' }}>
            Datasets: Jan Aushadhi (PMBJP 2026) • NPPA (DPCO 2013) • Rajya Sabha Session 255 • PMBI Kendra Network
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

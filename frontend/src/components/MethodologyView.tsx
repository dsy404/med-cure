import type { FC } from 'react';
import { Scale, Cpu, Search, FileText } from 'lucide-react';

export const MethodologyView: FC = () => {
  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f2744', marginBottom: '0.5rem' }}>
          Methodology & Architectural Principles
        </h2>
        <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          MedWise was engineered to solve the trust deficit in medicine search: replacing black-box AI chatbots with deterministic clinical verification, traceable price records, and explicit uncertainty handling.
        </p>
      </div>

      {/* Grid of Principles */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem', marginBottom: '3rem' }}>
        {/* Principle 1 */}
        <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <Scale className="w-6 h-6 text-teal-600" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f2744' }}>
              1. The "Evidence Over Confidence" Rule
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Never equate similar names with identical medicines, fuzzy-search similarity with clinical equivalence, or statutory ceiling caps with actual retail purchase quotes.
            The system returns explicit deterministic states:
          </p>
          <ul style={{ marginTop: '0.75rem', marginLeft: '1.5rem', fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            <li><strong>VERIFIED_FOR_PRICE_COMPARISON:</strong> Molecules, strengths, forms match, and both prices are comparable retail quotes.</li>
            <li><strong>NEEDS_CLARIFICATION:</strong> Strength, formulation, or release profile differs or was omitted by user.</li>
            <li><strong>INCOMPARABLE_PRICE_BASIS:</strong> Rejects comparing statutory ceiling caps against retail quotes.</li>
            <li><strong>INSUFFICIENT_EVIDENCE:</strong> Product price is listed as zero or reference data is absent.</li>
            <li><strong>NO_CATALOGUE_MATCH:</strong> System honestly abstains rather than returning arbitrary false matches.</li>
          </ul>
        </div>

        {/* Principle 2 */}
        <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <Search className="w-6 h-6 text-blue-600" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f2744' }}>
              2. Staged Multi-Tier Candidate Retrieval
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Search queries are evaluated through 6 staged phases rather than a single black-box embedding:
          </p>
          <ol style={{ marginTop: '0.75rem', marginLeft: '1.5rem', fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            <li><strong>Exact Match (100%):</strong> Strict case-insensitive product match.</li>
            <li><strong>Verified Brand Alias (98%):</strong> Ground-truth Indian brand mappings (e.g. Dolo 650 → Paracetamol 650mg, Augmentin 625 → Amoxicillin + Clavulanate).</li>
            <li><strong>Normalized Match (95%):</strong> Whitespace, typography, and punctuation normalization.</li>
            <li><strong>Token Containment (88%):</strong> Multi-word molecule and clinical attribute containment.</li>
            <li><strong>RapidFuzz Typo-Tolerance:</strong> Token sort ratio for misspelled words with strict minimum similarity thresholds.</li>
            <li><strong>Attribute-Aware Ranking:</strong> Prioritizes products matching stated dosage forms and positive listed prices.</li>
          </ol>
        </div>

        {/* Principle 3 */}
        <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <Cpu className="w-6 h-6 text-purple-600" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f2744' }}>
              3. Role & Boundaries of Local AI (Gemma)
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            The language model is deployed strictly as an auxiliary query interpreter, never as the arbiter of clinical truth or prices:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ background: '#ecfdf5', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid #a7f3d0' }}>
              <div style={{ fontWeight: 700, color: '#065f46', fontSize: '0.85rem', marginBottom: '0.25rem' }}>What Gemma Does:</div>
              <ul style={{ fontSize: '0.8rem', color: '#065f46', marginLeft: '1.2rem', lineHeight: 1.6 }}>
                <li>Interprets unstructured or misspelled user text</li>
                <li>Extracts explicitly mentioned strengths and forms</li>
                <li>Identifies missing clinical attributes</li>
                <li>Produces schema-validated JSON only</li>
              </ul>
            </div>
            <div style={{ background: '#fff1f2', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid #fecdd3' }}>
              <div style={{ fontWeight: 700, color: '#9f1239', fontSize: '0.85rem', marginBottom: '0.25rem' }}>What Gemma NEVER Does:</div>
              <ul style={{ fontSize: '0.8rem', color: '#9f1239', marginLeft: '1.2rem', lineHeight: 1.6 }}>
                <li>Never invents active molecules or prices</li>
                <li>Never establishes clinical equivalence</li>
                <li>Never computes savings calculations</li>
                <li>Cannot override failed deterministic verification</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Principle 4 */}
        <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <FileText className="w-6 h-6 text-teal-600" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f2744' }}>
              4. Authoritative Datasets & Price Types
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Every price displayed on MedWise is traceable to official government records:
          </p>
          <ul style={{ marginTop: '0.75rem', marginLeft: '1.5rem', fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            <li><strong>Jan Aushadhi Generic Medicines (PMBJP):</strong> 2,439 products with verified listed MRPs. 344 zero-MRP rows are explicitly quarantined from price calculations.</li>
            <li><strong>NPPA Statutory Ceiling Prices (DPCO 2013):</strong> 915 formulation ceiling caps fixed by statutory orders. These are legal price ceilings, not retail purchase prices.</li>
            <li><strong>Rajya Sabha Parliamentary Session 255 (Annexure 1784-B):</strong> Official surveyed average branded MRPs for market leaders submitted to Parliament by the Ministry of Chemicals and Fertilizers.</li>
          </ul>
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="safety-alert" style={{ marginBottom: '3rem' }}>
        <strong>Clinical & Regulatory Disclaimer:</strong> MedWise provides medicine price transparency and catalogue comparison tools only. It does not provide medical diagnosis, treatment advice, or prescription substitution authorization. Always consult a qualified registered medical practitioner or pharmacist before altering any medication regimen.
      </div>
    </div>
  );
};

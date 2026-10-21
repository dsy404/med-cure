import { useState, useRef } from 'react';
import type { FC, ChangeEvent } from 'react';
import {
  Camera,
  Upload,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Eye,
  ShieldCheck,
  Search
} from 'lucide-react';
import type { OCRPreviewResponse, MedicineProduct } from '../types';
import { uploadPackagingImage, getMedicineById, searchMedicines } from '../api';

interface ScanPackagingViewProps {
  onSelectCandidateForVerification: (candidate: MedicineProduct, queryText: string) => void;
  onAddPrescriptionItemFromScan: (text: string, candidateId?: string) => void;
}

export const ScanPackagingView: FC<ScanPackagingViewProps> = ({
  onSelectCandidateForVerification,
  onAddPrescriptionItemFromScan
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [ocrResult, setOcrResult] = useState<OCRPreviewResponse | null>(null);
  const [editedText, setEditedText] = useState<string>('');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [searchingCatalogue, setSearchingCatalogue] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showRawRegions, setShowRawRegions] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setErrorMsg('Please select a valid image file (JPEG, PNG, or WEBP).');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 10 MB limit.');
      return;
    }

    setErrorMsg(null);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setOcrResult(null);
    setCandidates([]);
  };

  const handleProcessImage = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setErrorMsg(null);

    try {
      const result = await uploadPackagingImage(selectedFile);
      setOcrResult(result);
      const draft = result.cleaned_draft_text || result.raw_extracted_text;
      setEditedText(draft);
      setCandidates(result.candidate_matches || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to process packaging image.');
    } finally {
      setUploading(false);
    }
  };

  const handleQuerySearch = async () => {
    const term = editedText.trim();
    if (!term) return;
    setSearchingCatalogue(true);
    try {
      const res = await searchMedicines(term, 6, true);
      const mapped = res.candidates.map((c) => ({
        product_id: c.product.product_id,
        name: c.product.name,
        catalogue_type: c.product.catalogue_type,
        unit_size: c.product.unit_size,
        mrp_inr: c.product.price ? c.product.price.amount_inr : 0.0,
        retrieval_method: c.retrieval_method,
        match_score: c.match_score,
        is_usable_for_comparison: c.product.price ? c.product.price.usable_for_comparison : false
      }));
      setCandidates(mapped);
    } catch (err: any) {
      console.error('Search catalogue error:', err);
    } finally {
      setSearchingCatalogue(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setOcrResult(null);
    setEditedText('');
    setCandidates([]);
    setErrorMsg(null);
  };

  const handleInspectCandidate = async (productId: string) => {
    try {
      const prod = await getMedicineById(productId);
      onSelectCandidateForVerification(prod, editedText);
    } catch (err) {
      console.error('Failed to load candidate product:', err);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f766e', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
          <Camera className="w-4 h-4" />
          <span>Visual Medicine Recognition Engine</span>
        </div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
          Scan Medicine Packaging & Blister Strips
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '720px' }}>
          Photograph printed medicine strip packaging to extract active salt names and strengths using local EasyOCR, assess image sharpness, review detected text, and match against verified Jan Aushadhi generic records.
        </p>
      </div>

      {/* Upload & Capture Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: previewUrl ? '1fr 1fr' : '1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Upload Box */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '2px dashed var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '2rem',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '260px'
          }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
          />
          <input
            type="file"
            ref={cameraInputRef}
            onChange={handleFileChange}
            accept="image/*"
            capture="environment"
            style={{ display: 'none' }}
          />

          {!previewUrl ? (
            <>
              <div style={{ background: '#f0fdfa', padding: '1rem', borderRadius: 'var(--radius-full)', marginBottom: '1rem' }}>
                <Upload className="w-8 h-8 text-teal-600" />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                Upload Packaging Photograph
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '380px', marginBottom: '1.25rem' }}>
                Capture printed medicine name, strength, and composition. Ensure lighting is clear and packaging text is in sharp focus.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="search-button"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.6rem 1.1rem', fontSize: '0.85rem' }}
                >
                  <Upload className="w-4 h-4" />
                  <span>Choose Image File</span>
                </button>
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.6rem 1.1rem',
                    color: 'var(--text-primary)',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem'
                  }}
                >
                  <Camera className="w-4 h-4 text-teal-600" />
                  <span>Take Photo</span>
                </button>
              </div>
            </>
          ) : (
            <div style={{ width: '100%' }}>
              <div style={{ position: 'relative', marginBottom: '1rem', maxHeight: '280px', overflow: 'hidden', borderRadius: 'var(--radius-lg)', background: '#000000' }}>
                <img
                  src={previewUrl}
                  alt="Packaging Preview"
                  style={{ width: '100%', height: '240px', objectFit: 'contain' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={handleReset}
                  style={{
                    background: 'none',
                    border: '1px solid var(--border-subtle)',
                    padding: '0.45rem 0.8rem',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-muted)',
                    fontSize: '0.8rem',
                    cursor: 'pointer'
                  }}
                >
                  Retake / Change Image
                </button>
                <button
                  type="button"
                  onClick={handleProcessImage}
                  disabled={uploading}
                  className="search-button"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 1.1rem', fontSize: '0.85rem' }}
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Analyzing Packaging...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Run OCR Extraction</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Quality Assessment & Extraction Status */}
        {ocrResult && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                <span>Physical Image Quality Audit</span>
              </h4>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.6rem',
                  borderRadius: 'var(--radius-full)',
                  background: ocrResult.quality.is_usable ? '#ecfdf5' : '#fffbeb',
                  color: ocrResult.quality.is_usable ? '#065f46' : '#92400e',
                  border: `1px solid ${ocrResult.quality.is_usable ? '#a7f3d0' : '#fde68a'}`
                }}
              >
                {ocrResult.quality.is_usable ? 'Quality Usable' : 'Quality Warnings'}
              </span>
            </div>

            {/* Quality Metrics Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
              <div style={{ background: 'var(--bg-app)', padding: '0.6rem', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Sharpness (Laplacian)</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: ocrResult.quality.is_blurry ? '#dc2626' : '#059669' }}>
                  {ocrResult.quality.blur_score}
                </div>
              </div>
              <div style={{ background: 'var(--bg-app)', padding: '0.6rem', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Lighting</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'capitalize' }}>
                  {ocrResult.quality.lighting_condition}
                </div>
              </div>
              <div style={{ background: 'var(--bg-app)', padding: '0.6rem', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Resolution</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>
                  {ocrResult.quality.resolution.width}x{ocrResult.quality.resolution.height}
                </div>
              </div>
            </div>

            {ocrResult.quality.warnings.length > 0 && (
              <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)', padding: '0.65rem', marginBottom: '1rem' }}>
                {ocrResult.quality.warnings.map((w, i) => (
                  <div key={i} style={{ fontSize: '0.78rem', color: '#92400e', display: 'flex', alignItems: 'flex-start', gap: '0.35rem', marginBottom: '0.2rem' }}>
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" style={{ marginTop: '2px' }} />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Detected Attributes Pills */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                Detected Attributes
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {ocrResult.detected_strengths.map((s, idx) => (
                  <span key={idx} style={{ background: '#f0fdfa', border: '1px solid #99f6e4', color: '#0f766e', fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-sm)' }}>
                    {s}
                  </span>
                ))}
                {ocrResult.detected_dosage_forms.map((f, idx) => (
                  <span key={idx} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1d4ed8', fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-sm)' }}>
                    {f}
                  </span>
                ))}
                {ocrResult.detected_strengths.length === 0 && ocrResult.detected_dosage_forms.length === 0 && (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    No specific strength or form detected automatically.
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {errorMsg && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-md)', padding: '0.75rem', marginBottom: '1.5rem', color: '#991b1b', fontSize: '0.85rem' }}>
          {errorMsg}
        </div>
      )}

      {/* Extraction Results & Matching Section */}
      {ocrResult && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '1.75rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Extracted Packaging Text & Candidate Generic Matches
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Engine: {ocrResult.ocr_engine} • Status: {ocrResult.processing_status}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowRawRegions(!showRawRegions)}
              style={{
                background: 'none',
                border: '1px solid var(--border-subtle)',
                padding: '0.35rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-secondary)',
                fontSize: '0.78rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>{showRawRegions ? 'Hide OCR Bounding Boxes' : 'Inspect Raw OCR Tokens'}</span>
            </button>
          </div>

          {/* Editable Draft Text (Human-in-the-loop review) */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
              Reviewed Medicine Query (Edit or correct extracted text before matching):
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleQuerySearch();
                }}
                placeholder="E.g. Dolo 650, Paracetamol 650mg, Augmentin 625..."
                style={{
                  flex: 1,
                  minWidth: '220px',
                  background: 'var(--bg-app)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.65rem 0.85rem',
                  fontSize: '0.92rem',
                  color: 'var(--text-primary)',
                  fontWeight: 600
                }}
              />
              <button
                type="button"
                onClick={handleQuerySearch}
                disabled={searchingCatalogue}
                className="search-button"
                style={{
                  whiteSpace: 'nowrap',
                  padding: '0.65rem 1rem',
                  fontSize: '0.85rem',
                  background: 'var(--primary-color)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem'
                }}
              >
                <Search className="w-4 h-4" />
                <span>{searchingCatalogue ? 'Searching...' : 'Search Catalogue'}</span>
              </button>
              <button
                type="button"
                onClick={() => onAddPrescriptionItemFromScan(editedText, candidates[0]?.product_id)}
                className="search-button"
                style={{ whiteSpace: 'nowrap', padding: '0.65rem 1rem', fontSize: '0.85rem' }}
              >
                + Add to Prescription
              </button>
            </div>
          </div>

          {/* Raw Regions Drawer */}
          {showRawRegions && (
            <div style={{ background: 'var(--bg-app)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '0.85rem', marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
                Raw Extracted OCR Tokens ({ocrResult.detected_regions.length} blocks)
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {ocrResult.detected_regions.map((reg, idx) => (
                  <span
                    key={idx}
                    title={`Confidence: ${(reg.confidence ? reg.confidence * 100 : 0).toFixed(1)}%`}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.2rem 0.5rem',
                      fontSize: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem'
                    }}
                  >
                    <span>{reg.text}</span>
                    <span style={{ fontSize: '0.65rem', color: '#0f766e', fontWeight: 700 }}>
                      {reg.confidence ? `${Math.round(reg.confidence * 100)}%` : ''}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Candidate Matches Retrieved from Genuine PMBJP Catalogue */}
          <div style={{ marginTop: '1.25rem' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
              Matched Catalogue Products ({candidates.length})
            </h4>

            {candidates.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No direct catalogue match found for extracted text. You can edit the query above and click "Search Catalogue".
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
                {candidates.map((cand) => (
                  <div
                    key={cand.product_id}
                    style={{
                      background: 'var(--bg-app)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#0f766e', background: '#f0fdfa', padding: '0.1rem 0.4rem', borderRadius: 'var(--radius-sm)' }}>
                          {cand.product_id}
                        </span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          Score: {Math.round(cand.match_score)}%
                        </span>
                      </div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                        {cand.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                        Pack: {cand.unit_size} • MRP: ₹{cand.mrp_inr.toFixed(2)}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleInspectCandidate(cand.product_id)}
                      className="verify-link-button"
                      style={{ width: '100%', justifyContent: 'center' }}
                    >
                      <span>Verify Match & View Evidence</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Safety Disclaimer */}
          <div style={{ marginTop: '1.25rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <b>Disclaimer:</b> {ocrResult.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};

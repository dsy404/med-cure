import type {
  SearchResponse,
  MedicineProduct,
  VerificationResult,
  BenchmarkReport,
  GemmaInterpretation,
  EvidenceGraphResponse,
  OCRPreviewResponse,
  PrescriptionResponse,
  PrescriptionItem,
  KendraSearchResponse
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch backend health status');
  return res.json();
}

export async function searchMedicines(
  query: string,
  limit: number = 10,
  includeCeiling: boolean = true
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    limit: limit.toString(),
    include_ceiling: includeCeiling.toString()
  });
  const res = await fetch(`${API_BASE}/medicines/search?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || 'Search request failed');
  }
  return res.json();
}

export async function getMedicineById(productId: string): Promise<MedicineProduct> {
  const res = await fetch(`${API_BASE}/medicines/${encodeURIComponent(productId)}`);
  if (!res.ok) throw new Error(`Medicine ${productId} not found`);
  return res.json();
}

export async function verifyCandidate(
  query: string,
  candidateProductId: string,
  userRefPrice?: number,
  userRefUnit?: string,
  referenceBrand?: string
): Promise<VerificationResult> {
  const payload = {
    query,
    candidate_product_id: candidateProductId,
    reference_brand_name: referenceBrand || null,
    user_reported_reference_price_inr: userRefPrice || null,
    user_reported_unit_size: userRefUnit || null
  };
  const res = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || 'Verification request failed');
  }
  return res.json();
}

export async function fetchEvidenceRecord(decisionId: string): Promise<EvidenceGraphResponse> {
  const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(decisionId)}`);
  if (!res.ok) throw new Error(`Evidence decision ${decisionId} not found`);
  return res.json();
}

export async function fetchRecentEvidence(limit: number = 20): Promise<any[]> {
  const res = await fetch(`${API_BASE}/evidence?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch recent evidence records');
  return res.json();
}

export async function uploadPackagingImage(file: File): Promise<OCRPreviewResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/recognition/preview`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Image OCR analysis failed');
  }
  return res.json();
}

export async function createPrescription(title?: string): Promise<PrescriptionResponse> {
  const params = title ? `?title=${encodeURIComponent(title)}` : '';
  const res = await fetch(`${API_BASE}/prescriptions${params}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to create prescription');
  return res.json();
}

export async function getPrescription(rxId: string): Promise<PrescriptionResponse> {
  const res = await fetch(`${API_BASE}/prescriptions/${encodeURIComponent(rxId)}`);
  if (!res.ok) throw new Error(`Prescription ${rxId} not found`);
  return res.json();
}

export async function addPrescriptionItem(
  rxId: string,
  item: {
    original_text: string;
    prescribed_name?: string;
    prescribed_strength?: string;
    prescribed_form?: string;
    prescribed_quantity?: number;
    user_reference_price_inr?: number;
    selected_candidate_id?: string;
  }
): Promise<PrescriptionItem> {
  const res = await fetch(`${API_BASE}/prescriptions/${encodeURIComponent(rxId)}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item)
  });
  if (!res.ok) throw new Error('Failed to add prescription item');
  return res.json();
}

export async function updatePrescriptionItem(
  rxId: string,
  itemId: string,
  update: {
    prescribed_name?: string;
    prescribed_strength?: string;
    prescribed_form?: string;
    prescribed_quantity?: number;
    user_reference_price_inr?: number;
    selected_candidate_id?: string;
  }
): Promise<PrescriptionItem> {
  const res = await fetch(`${API_BASE}/prescriptions/${encodeURIComponent(rxId)}/items/${encodeURIComponent(itemId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update)
  });
  if (!res.ok) throw new Error('Failed to update prescription item');
  return res.json();
}

export async function deletePrescriptionItem(rxId: string, itemId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/prescriptions/${encodeURIComponent(rxId)}/items/${encodeURIComponent(itemId)}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete prescription item');
  return res.json();
}

export function getPrescriptionPdfUrl(rxId: string): string {
  return `${API_BASE}/prescriptions/${encodeURIComponent(rxId)}/pdf`;
}

export async function searchKendras(
  query?: string,
  lat?: number,
  lng?: number,
  limit: number = 10
): Promise<KendraSearchResponse> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (lat !== undefined && lat !== null) params.append('lat', lat.toString());
  if (lng !== undefined && lng !== null) params.append('lng', lng.toString());
  params.append('limit', limit.toString());

  const res = await fetch(`${API_BASE}/locations/kendras?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to search Jan Aushadhi Kendras');
  return res.json();
}

export async function fetchOfficialBenchmarks(): Promise<any> {
  const res = await fetch(`${API_BASE}/benchmarks`);
  if (!res.ok) throw new Error('Failed to fetch official benchmarks');
  return res.json();
}

export async function runComparativeBenchmark(): Promise<BenchmarkReport> {
  const res = await fetch(`${API_BASE}/benchmark`);
  if (!res.ok) throw new Error('Failed to execute search benchmark');
  return res.json();
}

export async function fetchDataQualityReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/data-quality-report`);
  if (!res.ok) throw new Error('Failed to fetch data quality report');
  return res.json();
}

export async function fetchAiStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/ai/status`);
  if (!res.ok) throw new Error('Failed to check AI status');
  return res.json();
}

export async function interpretWithAi(query: string): Promise<GemmaInterpretation> {
  const res = await fetch(`${API_BASE}/ai/interpret?q=${encodeURIComponent(query)}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('AI interpretation request failed');
  return res.json();
}

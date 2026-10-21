export type RetrievalMethod =
  | 'EXACT_MATCH'
  | 'ALIAS_MATCH'
  | 'NORMALIZED_MATCH'
  | 'PARTIAL_MATCH'
  | 'FUZZY_MATCH'
  | 'NO_MATCH';

export type VerificationStatus =
  | 'VERIFIED_FOR_PRICE_COMPARISON'
  | 'NEEDS_CLARIFICATION'
  | 'INSUFFICIENT_EVIDENCE'
  | 'INCOMPARABLE_PRICE_BASIS'
  | 'NO_CATALOGUE_MATCH';

export type MatchConfidence = 'EXACT' | 'COMPATIBLE' | 'MISMATCH' | 'UNVERIFIED';

export interface PriceRecord {
  amount_inr: number;
  currency: string;
  unit_basis: string;
  price_type: string;
  price_status: string;
  usable_for_comparison: boolean;
  source_file: string;
  source_provenance: string;
  disclaimer: string;
}

export interface ExtractedAttributes {
  ingredients: string[];
  strengths: string[];
  dosage_form?: string | null;
  release_type?: string | null;
  pack_quantity?: string | null;
  explicitly_missing_attributes: string[];
}

export interface MedicineProduct {
  product_id: string;
  catalogue_type: 'generic_product' | 'ceiling_price_reference';
  name: string;
  brand_name?: string | null;
  therapeutic_group?: string | null;
  unit_size: string;
  price: PriceRecord;
  attributes: ExtractedAttributes;
  source_file: string;
  source_verification_status: string;
  duplicate_flag: boolean;
  metadata?: Record<string, any>;
}

export interface SearchCandidate {
  product: MedicineProduct;
  retrieval_method: RetrievalMethod;
  match_score: number;
  matched_term: string;
  notes?: string | null;
}

export interface SearchResponse {
  query: string;
  normalized_query: string;
  total_candidates: number;
  retrieval_strategy_applied: string;
  candidates: SearchCandidate[];
  message: string;
  execution_time_ms: number;
}

export interface AttributeVerificationItem {
  attribute_name: string;
  reference_value?: string | null;
  candidate_value?: string | null;
  is_match: boolean;
  confidence: MatchConfidence;
  details: string;
}

export interface PriceEvidence {
  source_organization: string;
  source_record_id: string;
  source_file: string;
  source_url?: string | null;
  price_type: string;
  amount_inr: number;
  unit_basis: string;
  effective_or_verified_date: string;
  limitations: string;
}

export interface SavingsBreakdown {
  is_eligible: boolean;
  ineligible_reason?: string | null;
  reference_price_inr?: number | null;
  comparison_price_inr?: number | null;
  normalized_unit_basis: string;
  absolute_saving_inr?: number | null;
  percentage_saving?: number | null;
  formula_applied: string;
  assumptions: string[];
}

export interface VerificationResult {
  decision_id?: string;
  evidence_chain_id?: string;
  verification_status: VerificationStatus;
  query: string;
  candidate_id: string;
  candidate_name: string;
  candidate_catalogue_type: string;
  attribute_checks: AttributeVerificationItem[];
  reference_price_evidence?: PriceEvidence | null;
  comparison_price_evidence?: PriceEvidence | null;
  savings: SavingsBreakdown;
  clinical_disclaimer: string;
  plain_language_summary: string;
  verified_at: string;
}

export interface InputEvidenceNode {
  input_id: string;
  query: string;
  input_type: string;
  user_reported_price_inr?: number | null;
  user_reported_unit?: string | null;
  reference_brand?: string | null;
  captured_at: string;
}

export interface ExtractionNode {
  normalized_query: string;
  detected_molecules: string[];
  detected_strengths: string[];
  detected_dosage_form?: string | null;
  brand_alias_applied?: string | null;
  is_combination: boolean;
}

export interface CandidateNode {
  product_id: string;
  name: string;
  catalogue_type: string;
  retrieval_method: string;
  unit_size: string;
  mrp_inr: number;
  source_file: string;
  provenance: string;
}

export interface DecisionNode {
  decision_id: string;
  verification_status: VerificationStatus;
  is_savings_eligible: boolean;
  summary: string;
  abstention_reason?: string | null;
  verified_at: string;
  disclaimer: string;
}

export interface EvidenceGraphResponse {
  decision_id: string;
  input_evidence: InputEvidenceNode;
  extraction: ExtractionNode;
  candidate: CandidateNode;
  attribute_checks: AttributeVerificationItem[];
  price_evidence?: PriceEvidence | null;
  savings: SavingsBreakdown;
  decision: DecisionNode;
  software_version: string;
  clinical_disclaimer: string;
}

export interface TextRegion {
  text: string;
  confidence?: number | null;
  bounding_box?: number[][] | null;
}

export interface ImageQualityAssessment {
  is_usable: boolean;
  blur_score: number;
  is_blurry: boolean;
  brightness_score: number;
  lighting_condition: string;
  resolution: { width: number; height: number };
  warnings: string[];
}

export interface OCRPreviewResponse {
  ocr_engine: string;
  processing_status: string;
  quality: ImageQualityAssessment;
  raw_extracted_text: string;
  cleaned_draft_text: string;
  detected_regions: TextRegion[];
  detected_strengths: string[];
  detected_dosage_forms: string[];
  candidate_matches: Array<{
    product_id: string;
    name: string;
    catalogue_type: string;
    unit_size: string;
    mrp_inr: number;
    retrieval_method: string;
    match_score: number;
    is_usable_for_comparison: boolean;
  }>;
  disclaimer: string;
}

export interface PrescriptionItem {
  item_id: string;
  prescription_id: string;
  original_text: string;
  prescribed_name: string;
  prescribed_strength?: string | null;
  prescribed_form?: string | null;
  prescribed_quantity: number;
  user_reference_price_inr?: number | null;
  candidate_id?: string | null;
  candidate_name?: string | null;
  candidate_mrp_inr?: number | null;
  candidate_unit_size?: string | null;
  verification_status: string;
  is_eligible_for_savings: boolean;
  reference_price_inr?: number | null;
  comparison_price_inr?: number | null;
  calculated_saving_inr?: number | null;
  percentage_saving?: number | null;
  evidence_decision_id?: string | null;
  ineligible_reason?: string | null;
  clarification_status: string;
  created_at: string;
}

export interface PrescriptionSummary {
  total_items_count: number;
  verified_comparisons_count: number;
  unresolved_items_count: number;
  excluded_items_count: number;
  confirmed_total_savings_inr: number;
  confirmed_reference_spend_inr: number;
  confirmed_generic_spend_inr: number;
  confirmed_savings_percentage: number;
  unresolved_summary: string;
  excluded_potential_savings_inr?: number | null;
  excluded_potential_savings_note?: string;
}

export interface PrescriptionResponse {
  prescription_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  items: PrescriptionItem[];
  summary: PrescriptionSummary;
  disclaimer: string;
}

export interface JanAushadhiKendra {
  kendra_id: string;
  kendra_name: string;
  address: string;
  city_or_district: string;
  state: string;
  pincode: string;
  contact_number?: string | null;
  latitude: number;
  longitude: number;
  distance_km?: number | null;
  operating_hours: string;
  source_attribution: string;
  data_freshness: string;
  directions_url?: string | null;
}

export interface KendraSearchResponse {
  query?: string | null;
  user_latitude?: number | null;
  user_longitude?: number | null;
  total_results: number;
  search_note?: string | null;
  kendras: JanAushadhiKendra[];
  stock_verification_disclaimer: string;
}

export interface GemmaInterpretation {
  is_available: boolean;
  model_name?: string | null;
  interpreted_name?: string | null;
  possible_names: string[];
  strength_mentioned?: string | null;
  dosage_form_mentioned?: string | null;
  missing_attributes: string[];
  needs_clarification: boolean;
  reason: string;
  execution_time_ms: number;
}

export interface BenchmarkReport {
  total_test_cases: number;
  ollama_status: {
    ollama_online: boolean;
    available_models: string[];
    target_model: string;
    target_model_installed: boolean;
    status_message: string;
  };
  mode_a_exact: {
    top1_accuracy: number;
    top3_recall: number;
    correct_abstention_rate: number;
    avg_latency_ms: number;
  };
  mode_b_fuzzy_deterministic: {
    top1_accuracy: number;
    top3_recall: number;
    correct_abstention_rate: number;
    avg_latency_ms: number;
  };
  mode_c_gemma_assisted: {
    top1_accuracy: number;
    top3_recall: number;
    correct_abstention_rate: number;
    avg_latency_ms: number;
    model_status: string;
  };
  comparison_summary: string;
  detailed_results: Array<{
    case: {
      query: string;
      category: string;
      description: string;
    };
    mode_a_hit: boolean;
    mode_b_hit: boolean;
    mode_c_hit: boolean;
    gemma_available: boolean;
    latency_a_ms: number;
    latency_b_ms: number;
    latency_c_ms: number;
  }>;
}

export interface BasketItem {
  id: string;
  query: string;
  candidate: MedicineProduct;
  verification: VerificationResult;
}

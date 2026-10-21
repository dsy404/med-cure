from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .verification import AttributeVerificationItem, PriceEvidence, SavingsBreakdown
from .medicine import VerificationStatus

class InputEvidenceNode(BaseModel):
    input_id: str
    query: str
    input_type: str = "typed_search"  # typed_search, ocr_scan, prescription_line
    user_reported_price_inr: Optional[float] = None
    user_reported_unit: Optional[str] = None
    reference_brand: Optional[str] = None
    captured_at: str

class ExtractionNode(BaseModel):
    normalized_query: str
    detected_molecules: List[str] = Field(default_factory=list)
    detected_strengths: List[str] = Field(default_factory=list)
    detected_dosage_form: Optional[str] = None
    brand_alias_applied: Optional[str] = None
    is_combination: bool = False

class CandidateNode(BaseModel):
    product_id: str
    name: str
    catalogue_type: str
    retrieval_method: str
    unit_size: str
    mrp_inr: float
    source_file: str
    provenance: str

class DecisionNode(BaseModel):
    decision_id: str
    verification_status: VerificationStatus
    is_savings_eligible: bool
    summary: str
    abstention_reason: Optional[str] = None
    verified_at: str
    disclaimer: str

class EvidenceGraphResponse(BaseModel):
    decision_id: str
    input_evidence: InputEvidenceNode
    extraction: ExtractionNode
    candidate: CandidateNode
    attribute_checks: List[AttributeVerificationItem]
    price_evidence: Optional[PriceEvidence] = None
    savings: SavingsBreakdown
    decision: DecisionNode
    software_version: str = "MedWise v2.0.0"
    clinical_disclaimer: str

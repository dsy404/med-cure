from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .medicine import VerificationStatus, PriceType

class MatchConfidence(str, Enum):
    EXACT = "EXACT"
    COMPATIBLE = "COMPATIBLE"
    MISMATCH = "MISMATCH"
    UNVERIFIED = "UNVERIFIED"

class AttributeVerificationItem(BaseModel):
    attribute_name: str
    reference_value: Optional[str] = None
    candidate_value: Optional[str] = None
    is_match: bool
    confidence: MatchConfidence
    details: str

class PriceEvidence(BaseModel):
    source_organization: str
    source_record_id: str
    source_file: str
    source_url: Optional[str] = None
    price_type: str
    amount_inr: float
    unit_basis: str
    effective_or_verified_date: str
    limitations: str

class SavingsBreakdown(BaseModel):
    is_eligible: bool
    ineligible_reason: Optional[str] = None
    reference_price_inr: Optional[float] = None
    comparison_price_inr: Optional[float] = None
    normalized_unit_basis: str
    absolute_saving_inr: Optional[float] = None
    percentage_saving: Optional[float] = None
    formula_applied: str
    assumptions: List[str] = Field(default_factory=list)

class VerificationResult(BaseModel):
    decision_id: str = Field(default_factory=lambda: "DEC-TEMP")
    evidence_chain_id: str = Field(default_factory=lambda: "EVD-CHAIN")
    verification_status: VerificationStatus
    query: str
    candidate_id: str
    candidate_name: str
    candidate_catalogue_type: str
    attribute_checks: List[AttributeVerificationItem]
    reference_price_evidence: Optional[PriceEvidence] = None
    comparison_price_evidence: Optional[PriceEvidence] = None
    savings: SavingsBreakdown
    clinical_disclaimer: str = (
        "MedLedger provides medicine catalogue and price-comparison information. "
        "It does not diagnose conditions, prescribe treatment, confirm medicine authenticity, "
        "or determine whether a medicine is suitable for an individual. "
        "Discuss possible medicine changes with a qualified pharmacist or prescriber."
    )
    plain_language_summary: str
    verified_at: str

class VerificationRequest(BaseModel):
    query: str
    candidate_product_id: str
    reference_brand_name: Optional[str] = None
    user_reported_reference_price_inr: Optional[float] = None
    user_reported_unit_size: Optional[str] = None

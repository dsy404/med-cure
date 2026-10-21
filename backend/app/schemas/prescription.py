from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PrescriptionItemCreate(BaseModel):
    original_text: str
    prescribed_name: Optional[str] = None
    prescribed_strength: Optional[str] = None
    prescribed_form: Optional[str] = None
    prescribed_quantity: Optional[float] = 10.0
    user_reference_price_inr: Optional[float] = None
    selected_candidate_id: Optional[str] = None

class PrescriptionItemUpdate(BaseModel):
    prescribed_name: Optional[str] = None
    prescribed_strength: Optional[str] = None
    prescribed_form: Optional[str] = None
    prescribed_quantity: Optional[float] = None
    user_reference_price_inr: Optional[float] = None
    selected_candidate_id: Optional[str] = None
    clarification_notes: Optional[str] = None

class PrescriptionItem(BaseModel):
    item_id: str
    prescription_id: str
    original_text: str
    prescribed_name: str
    prescribed_strength: Optional[str] = None
    prescribed_form: Optional[str] = None
    prescribed_quantity: float = 10.0
    user_reference_price_inr: Optional[float] = None
    
    # Candidate details
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_mrp_inr: Optional[float] = None
    candidate_unit_size: Optional[str] = None
    
    # Verification details
    verification_status: str = "NEEDS_CLARIFICATION"
    is_eligible_for_savings: bool = False
    reference_price_inr: Optional[float] = None
    comparison_price_inr: Optional[float] = None
    calculated_saving_inr: Optional[float] = None
    percentage_saving: Optional[float] = None
    evidence_decision_id: Optional[str] = None
    ineligible_reason: Optional[str] = None
    clarification_status: str = "unresolved"  # "resolved", "unresolved", "manually_confirmed"
    created_at: str

class PrescriptionSummary(BaseModel):
    total_items_count: int
    verified_comparisons_count: int
    unresolved_items_count: int
    excluded_items_count: int
    
    # Total A: Evidence-supported confirmed savings
    confirmed_total_savings_inr: float
    confirmed_reference_spend_inr: float
    confirmed_generic_spend_inr: float
    confirmed_savings_percentage: float
    
    # Total B: Unresolved items explanation
    unresolved_summary: str
    
    # Total C: Potential savings excluded from confirmed total
    excluded_potential_savings_inr: Optional[float] = None
    excluded_potential_savings_note: str = (
        "Calculated only as an informational estimate for unresolved items. "
        "Strictly EXCLUDED from confirmed total savings until attributes or prices are verified."
    )

class PrescriptionResponse(BaseModel):
    prescription_id: str
    title: str
    created_at: str
    updated_at: str
    items: List[PrescriptionItem] = Field(default_factory=list)
    summary: PrescriptionSummary
    disclaimer: str = (
        "MedLedger prescription price calculations are informational comparisons based on public DPCO "
        "and PMBJP datasets. They do not constitute an order, prescription, or clinical substitution directive. "
        "Consult your licensed physician or pharmacist before changing any prescribed medication."
    )

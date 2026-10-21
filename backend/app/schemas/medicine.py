from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RetrievalMethod(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    ALIAS_MATCH = "ALIAS_MATCH"
    NORMALIZED_MATCH = "NORMALIZED_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    NO_MATCH = "NO_MATCH"

class VerificationStatus(str, Enum):
    VERIFIED_FOR_PRICE_COMPARISON = "VERIFIED_FOR_PRICE_COMPARISON"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INCOMPARABLE_PRICE_BASIS = "INCOMPARABLE_PRICE_BASIS"
    NO_CATALOGUE_MATCH = "NO_CATALOGUE_MATCH"

class PriceType(str, Enum):
    MAXIMUM_RETAIL_PRICE = "maximum_retail_price_mrp"
    CEILING_PRICE = "ceiling_price_excluding_taxes"
    GOVERNMENT_PROCUREMENT = "government_procurement_price"
    REFERENCE_BENCHMARK = "reference_benchmark_price"
    UNKNOWN = "unknown"

class PriceRecord(BaseModel):
    amount_inr: float
    currency: str = "INR"
    unit_basis: str
    price_type: str
    price_status: str
    usable_for_comparison: bool
    source_file: str
    source_provenance: str
    disclaimer: str

class ExtractedAttributes(BaseModel):
    ingredients: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    dosage_form: Optional[str] = None
    release_type: Optional[str] = None
    pack_quantity: Optional[str] = None
    explicitly_missing_attributes: List[str] = Field(default_factory=list)

class MedicineProduct(BaseModel):
    product_id: str
    catalogue_type: str # "generic_product" | "ceiling_price_reference"
    name: str
    brand_name: Optional[str] = None
    therapeutic_group: Optional[str] = None
    unit_size: str
    price: PriceRecord
    attributes: ExtractedAttributes
    source_file: str
    source_verification_status: str
    duplicate_flag: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchCandidate(BaseModel):
    product: MedicineProduct
    retrieval_method: RetrievalMethod
    match_score: float = Field(..., ge=0.0, le=100.0)
    matched_term: str
    notes: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    total_candidates: int
    retrieval_strategy_applied: str
    candidates: List[SearchCandidate]
    message: str
    execution_time_ms: float

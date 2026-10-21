from typing import List, Optional
from pydantic import BaseModel, Field

class GemmaInterpretation(BaseModel):
    is_available: bool = False
    model_name: Optional[str] = None
    interpreted_name: Optional[str] = None
    possible_names: List[str] = Field(default_factory=list)
    strength_mentioned: Optional[str] = None
    dosage_form_mentioned: Optional[str] = None
    missing_attributes: List[str] = Field(default_factory=list)
    needs_clarification: bool = True
    reason: str = "Deterministic fallback; AI model unavailable or offline"
    execution_time_ms: float = 0.0

class ComparativeBenchmarkResult(BaseModel):
    query: str
    ground_truth: str
    mode_a_exact_top1: bool
    mode_b_fuzzy_top1: bool
    mode_c_gemma_top1: bool
    mode_a_latency_ms: float
    mode_b_latency_ms: float
    mode_c_latency_ms: float
    notes: str

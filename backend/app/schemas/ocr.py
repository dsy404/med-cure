from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TextRegion(BaseModel):
    text: str
    confidence: Optional[float] = None
    bounding_box: Optional[List[List[int]]] = None

class ImageQualityAssessment(BaseModel):
    is_usable: bool
    blur_score: float
    is_blurry: bool
    brightness_score: float
    lighting_condition: str  # optimal, too_dark, too_bright
    resolution: Dict[str, int]
    warnings: List[str] = Field(default_factory=list)

class OCRPreviewResponse(BaseModel):
    ocr_engine: str = "EasyOCR 1.7.2"
    processing_status: str  # SUCCESS, PARTIAL, POOR_IMAGE_QUALITY, FAILED
    quality: ImageQualityAssessment
    raw_extracted_text: str
    cleaned_draft_text: str
    detected_regions: List[TextRegion] = Field(default_factory=list)
    detected_strengths: List[str] = Field(default_factory=list)
    detected_dosage_forms: List[str] = Field(default_factory=list)
    candidate_matches: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = (
        "Packaging OCR extraction is assistive and unverified. Packaging text must be confirmed "
        "by the user before clinical matching. Packaging recognition does not guarantee medicine authenticity."
    )

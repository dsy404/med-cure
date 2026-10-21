import re
import io
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from ..schemas.ocr import (
    TextRegion,
    ImageQualityAssessment,
    OCRPreviewResponse
)
from .normalizer import STRENGTH_REGEX, DOSAGE_FORMS
from .medicine_search import MedicineSearchEngine
from .brand_aliases import BRAND_ALIASES

logger = logging.getLogger(__name__)

# Lazy-loaded EasyOCR reader to avoid slow startup
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                except Exception:
                    pass
            import easyocr
            # Using CPU to ensure 100% deterministic portability without requiring CUDA
            # verbose=False prevents Windows stdout charmap/progress-bar encoding failures
            _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR English CPU reader initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR reader: {e}")
            _easyocr_reader = None
    return _easyocr_reader


class OCRService:
    def __init__(self, search_engine: Optional[MedicineSearchEngine] = None):
        self.search_engine = search_engine

    def assess_image_quality(self, img_np: np.ndarray) -> ImageQualityAssessment:
        """
        Assesses blur, resolution, and brightness before running OCR.
        Uses Laplacian variance for blur and mean intensity for lighting.
        """
        h, w = img_np.shape[:2]
        warnings: List[str] = []
        
        # Convert to grayscale for analysis
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # 1. Blur evaluation via Laplacian variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < 45.0
        if is_blurry:
            warnings.append(
                f"Image sharpness score is low ({laplacian_var:.1f}). Focus may be soft; verify text before matching."
            )

        # 2. Lighting / brightness evaluation
        mean_brightness = float(np.mean(gray))
        if mean_brightness < 40.0:
            lighting = "too_dark"
            warnings.append(f"Image appears underexposed (brightness {mean_brightness:.1f}/255). Ensure adequate illumination.")
        elif mean_brightness > 220.0:
            lighting = "too_bright"
            warnings.append(f"Image appears overexposed (brightness {mean_brightness:.1f}/255). Glare on packaging may obscure print.")
        else:
            lighting = "optimal"

        # 3. Resolution check
        if w < 220 or h < 220:
            warnings.append(f"Image dimensions ({w}x{h} px) are very low. Fine print and salt strengths may be illegible.")

        is_usable = (not is_blurry) and (w >= 160) and (h >= 160) and (lighting != "too_dark")

        return ImageQualityAssessment(
            is_usable=is_usable,
            blur_score=round(laplacian_var, 2),
            is_blurry=is_blurry,
            brightness_score=round(mean_brightness, 2),
            lighting_condition=lighting,
            resolution={"width": w, "height": h},
            warnings=warnings
        )

    def process_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> OCRPreviewResponse:
        """
        Validates, assesses, and extracts text from an uploaded packaging photo.
        Returns extracted lines, confidence scores, and potential catalogue matches.
        """
        if not image_bytes or len(image_bytes) < 100:
            return OCRPreviewResponse(
                processing_status="FAILED",
                quality=ImageQualityAssessment(
                    is_usable=False,
                    blur_score=0.0,
                    is_blurry=True,
                    brightness_score=0.0,
                    lighting_condition="unusable",
                    resolution={"width": 0, "height": 0},
                    warnings=["Empty or corrupted image payload received."]
                ),
                raw_extracted_text="",
                cleaned_draft_text="",
                candidate_matches=[]
            )

        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            pil_image = pil_image.convert("RGB")
            img_np = np.array(pil_image)
        except Exception as e:
            logger.error(f"Failed to decode image bytes: {e}")
            return OCRPreviewResponse(
                processing_status="FAILED",
                quality=ImageQualityAssessment(
                    is_usable=False,
                    blur_score=0.0,
                    is_blurry=True,
                    brightness_score=0.0,
                    lighting_condition="corrupted",
                    resolution={"width": 0, "height": 0},
                    warnings=[f"Could not parse image format: {str(e)}"]
                ),
                raw_extracted_text="",
                cleaned_draft_text="",
                candidate_matches=[]
            )

        # Assess physical image quality
        quality = self.assess_image_quality(img_np)

        # Run OCR extraction
        reader = get_easyocr_reader()
        detected_regions: List[TextRegion] = []
        raw_lines: List[str] = []

        if reader is not None:
            try:
                # Primary pass: raw color image
                results = reader.readtext(img_np)

                # Secondary pass: CLAHE (Contrast-Limited Adaptive Histogram Equalization)
                # Blister strips and foil packaging exhibit specular glare / overexposure
                if quality.lighting_condition == "too_bright" or len(results) < 3 or quality.brightness_score > 190.0:
                    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    enhanced = clahe.apply(gray)
                    clahe_results = reader.readtext(enhanced)

                    # Deduplicate and combine detected tokens
                    seen_texts = {r[1].strip().lower() for r in results}
                    for bbox, text, prob in clahe_results:
                        t_clean = str(text).strip()
                        if t_clean and t_clean.lower() not in seen_texts:
                            results.append((bbox, text, prob))
                            seen_texts.add(t_clean.lower())

                for bbox, text, prob in results:
                    text_clean = str(text).strip()
                    if text_clean:
                        clean_bbox = [[int(pt[0]), int(pt[1])] for pt in bbox]
                        detected_regions.append(TextRegion(
                            text=text_clean,
                            confidence=round(float(prob), 4),
                            bounding_box=clean_bbox
                        ))
                        raw_lines.append(text_clean)
            except Exception as ocr_err:
                logger.error(f"EasyOCR extraction exception: {ocr_err}")
                quality.warnings.append(f"OCR execution encountered an internal error: {str(ocr_err)}")

        raw_text = " ".join(raw_lines)
        cleaned_draft = self._formulate_draft_medicine_query(raw_lines, raw_text)

        # Extract attributes
        strengths = self._extract_strengths(raw_text + " " + cleaned_draft)
        forms = self._extract_dosage_forms(raw_text + " " + cleaned_draft)

        # Retrieve candidates if search engine is available
        candidate_matches: List[Dict[str, Any]] = []
        if self.search_engine and (cleaned_draft.strip() or raw_text.strip()):
            query_to_search = cleaned_draft if cleaned_draft.strip() else raw_text
            search_res = self.search_engine.search(query=query_to_search, limit=5, include_ceiling_prices=True)

            # Fallback search if draft yielded no direct matches
            if not search_res.candidates and raw_text.strip():
                cleaned_fallback = self._clean_ocr_text(raw_text)
                search_res = self.search_engine.search(query=cleaned_fallback, limit=5, include_ceiling_prices=True)

            candidate_matches = [
                {
                    "product_id": c.product.product_id,
                    "name": c.product.name,
                    "catalogue_type": c.product.catalogue_type,
                    "unit_size": c.product.unit_size,
                    "mrp_inr": c.product.price.amount_inr if c.product.price else 0.0,
                    "retrieval_method": c.retrieval_method.value,
                    "match_score": c.match_score,
                    "is_usable_for_comparison": c.product.price.usable_for_comparison if c.product.price else False
                }
                for c in search_res.candidates
            ]

        status = "SUCCESS" if raw_lines else ("POOR_IMAGE_QUALITY" if not quality.is_usable else "PARTIAL")

        return OCRPreviewResponse(
            ocr_engine="EasyOCR 1.7.2 (PyTorch CPU)",
            processing_status=status,
            quality=quality,
            raw_extracted_text=raw_text,
            cleaned_draft_text=cleaned_draft,
            detected_regions=detected_regions,
            detected_strengths=strengths,
            detected_dosage_forms=forms,
            candidate_matches=candidate_matches
        )

    def _formulate_draft_medicine_query(self, raw_lines: List[str], full_text: str) -> str:
        """
        Extracts high-relevance clinical medicine search term from packaging OCR.
        Prioritizes:
        1. Known brand name aliases (e.g. 'Dolo 650', 'Crocin 650', 'Calpol 500')
        2. Known active salt + strength (e.g. 'Paracetamol 650 mg', 'Metformin 500 mg')
        3. Cleaned high-signal packaging tokens minus manufacturing boilerplate
        """
        if not full_text.strip():
            return ""

        # Pre-clean typical blister-pack numeral confusions
        # E.g. 'Dolo-050' or 'Dolo-O50' -> 'Dolo-650'
        text_for_search = re.sub(r'\b(dolo)[-\s]*[0O]50\b', r'\1 650', full_text, flags=re.IGNORECASE)
        text_for_search = re.sub(r'(\w+)-(\d+)', r'\1 \2', text_for_search)

        # 1. Check known brand aliases
        for brand_key in sorted(BRAND_ALIASES.keys(), key=len, reverse=True):
            pattern = r'\b' + re.escape(brand_key) + r'\b'
            if re.search(pattern, text_for_search, re.IGNORECASE):
                return BRAND_ALIASES[brand_key].brand_name

        # 2. Check active salts and strengths
        salts = [
            "paracetamol", "amoxicillin", "metformin", "atorvastatin",
            "azithromycin", "pantoprazole", "ibuprofen", "cetirizine",
            "omeprazole", "telmisartan", "amlodipine", "losartan",
            "ciprofloxacin", "ranitidine", "diclofenac", "aspirin"
        ]
        found_salt = None
        for s in salts:
            if re.search(r'\b' + s + r'\b', text_for_search, re.IGNORECASE):
                found_salt = s.capitalize()
                break

        strengths = self._extract_strengths(text_for_search)
        forms = self._extract_dosage_forms(text_for_search)

        if found_salt and strengths:
            form_str = f" {forms[0]}" if forms else " Tablet"
            return f"{found_salt} {strengths[0]}{form_str}"
        elif found_salt:
            form_str = f" {forms[0]}" if forms else ""
            return f"{found_salt}{form_str}"

        # 3. Filter out manufacturing boilerplate phrases
        boilerplate_terms = {
            "mfg", "lic", "batch", "mrp", "exp", "store", "dosage",
            "physician", "injurious", "directed", "keep out", "children",
            "marketed", "manufactured", "limited", "ltd", "pack", "warning",
            "schedule", "prescription", "dry", "dark", "place"
        }
        filtered_tokens = []
        for line in raw_lines:
            line_clean = line.strip()
            words = [w.lower() for w in re.findall(r'\b\w+\b', line_clean)]
            if words and any(w in boilerplate_terms for w in words):
                continue
            if len(line_clean) >= 2:
                filtered_tokens.append(line_clean)

        if filtered_tokens:
            return self._clean_ocr_text(" ".join(filtered_tokens[:3]))

        return self._clean_ocr_text(full_text)

    def _clean_ocr_text(self, text: str) -> str:
        """
        Deterministically cleans noisy OCR tokens while strictly preserving numbers, units, and words.
        Corrects common OCR numeral-letter confusions in dosage contexts (e.g., '1O mg' -> '10 mg').
        """
        if not text:
            return ""
        
        # Replace non-ascii artifacts
        cleaned = re.sub(r"[^\w\s\.,\-\+/]", " ", text)
        
        # Correct typical OCR digit/letter confusions in dosage patterns
        cleaned = re.sub(r"\b(\d+)[Oo]\s*(mg|mcg|g|ml)\b", r"\g<1>0 \2", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b1[Oo][Oo]\s*(mg|mcg|g|ml)\b", r"100 \1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b[lI][oO]\s*(mg|mcg|g|ml)\b", r"10 \1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b[lI](\d+)\s*(mg|mcg|g|ml)\b", r"1\1 \2", cleaned, flags=re.IGNORECASE)
        
        # Collapse multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _extract_strengths(self, text: str) -> List[str]:
        found: List[str] = []
        for match in STRENGTH_REGEX.finditer(text):
            val = match.group(0).strip()
            if val and val.lower() not in [f.lower() for f in found]:
                found.append(val)
        return found

    def _extract_dosage_forms(self, text: str) -> List[str]:
        found: List[str] = []
        t_lower = text.lower()
        for form in DOSAGE_FORMS:
            if re.search(r"\b" + re.escape(form) + r"\b", t_lower):
                capitalized = form.capitalize()
                if capitalized not in found:
                    found.append(capitalized)
        return found


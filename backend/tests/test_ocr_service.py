import numpy as np
import pytest
from app.services.ocr_service import OCRService

@pytest.fixture
def ocr_service():
    return OCRService(search_engine=None)

def test_ocr_clean_text_dosage_confusions(ocr_service):
    # Test OCR numeral-letter corrections
    # 1O mg -> 10 mg
    assert ocr_service._clean_ocr_text("ATORVASTATIN 1O MG") == "ATORVASTATIN 10 MG"
    # 5O mg -> 50 mg
    assert ocr_service._clean_ocr_text("METFORMIN 5O mg") == "METFORMIN 50 mg"
    # 1OO mg -> 100 mg
    assert ocr_service._clean_ocr_text("ACECLOFENAC 1OO MG") == "ACECLOFENAC 100 MG"
    # lO mg -> 10 mg
    assert ocr_service._clean_ocr_text("ATORVASTATIN lO mg") == "ATORVASTATIN 10 mg"

def test_ocr_extract_strengths(ocr_service):
    text = "PARACETAMOL TABLETS IP 650 MG STRIP OF 10 TABLETS"
    strengths = ocr_service._extract_strengths(text)
    assert any("650" in s for s in strengths)

def test_ocr_extract_dosage_forms(ocr_service):
    text = "Atorvastatin 10mg Tablets IP"
    forms = ocr_service._extract_dosage_forms(text)
    assert any("tablet" in f.lower() for f in forms)

def test_assess_image_quality_sharp_and_blurry(ocr_service):
    # Create synthetic sharp image with high frequency edges
    sharp_img = np.zeros((300, 300, 3), dtype=np.uint8)
    sharp_img[::2, ::2] = 255
    q_sharp = ocr_service.assess_image_quality(sharp_img)
    assert q_sharp.is_blurry is False
    assert q_sharp.blur_score > 45.0

    # Create uniform flat image (zero edges -> blurred)
    flat_img = np.full((300, 300, 3), 128, dtype=np.uint8)
    q_flat = ocr_service.assess_image_quality(flat_img)
    assert q_flat.is_blurry is True
    assert q_flat.blur_score < 45.0
    assert any("sharpness" in w.lower() for w in q_flat.warnings)

def test_formulate_draft_medicine_query_brand(ocr_service):
    raw_lines = ["Paracetamol", "Tablets IP", "Dolo-650", "Micro Labs"]
    full_text = "Paracetamol Tablets IP Dolo-650 Micro Labs"
    query = ocr_service._formulate_draft_medicine_query(raw_lines, full_text)
    assert query == "Dolo 650"

def test_formulate_draft_medicine_query_blister_numeral_correction(ocr_service):
    # When blister glare causes 'Dolo-050' or 'Dolo-O50'
    raw_lines = ["Paracetamol", "Tablets IP", "Dolo-050"]
    full_text = "Paracetamol Tablets IP Dolo-050"
    query = ocr_service._formulate_draft_medicine_query(raw_lines, full_text)
    assert query == "Dolo 650"

def test_formulate_draft_medicine_query_generic_salt(ocr_service):
    raw_lines = ["Paracetamol 650 mg", "Batch No. 123", "Store below 30C"]
    full_text = "Paracetamol 650 mg Batch No. 123 Store below 30C"
    query = ocr_service._formulate_draft_medicine_query(raw_lines, full_text)
    assert "Paracetamol 650 mg" in query


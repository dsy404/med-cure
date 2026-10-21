import pytest
from app.services.normalizer import normalize_text, extract_attributes

def test_normalize_text():
    assert normalize_text("  Paracetamol   500MG  ") == "paracetamol 500mg"
    assert normalize_text("Aspirin – Gastro-Resistant") == "aspirin - gastro-resistant"
    assert normalize_text("") == ""
    assert normalize_text("   \n\t  ") == ""

def test_extract_attributes_single_ingredient():
    attrs = extract_attributes("Aceclofenac Tablets IP 100 mg", "10's")
    assert "100mg" in attrs.strengths
    assert attrs.dosage_form == "Tablets"
    assert attrs.pack_quantity == "10's"
    assert "Aceclofenac" in attrs.ingredients
    assert "brand_name" in attrs.explicitly_missing_attributes
    assert "manufacturer" in attrs.explicitly_missing_attributes

def test_extract_attributes_combination():
    raw = "Aceclofenac 100mg and Paracetamol 325mg Tablets"
    attrs = extract_attributes(raw, "10's")
    assert "100mg" in attrs.strengths
    assert "325mg" in attrs.strengths
    assert attrs.dosage_form == "Tablets"
    assert len(attrs.ingredients) >= 2

def test_extract_release_formulation():
    raw = "Diclofenac Sodium Prolonged Release Tablets IP 100 mg"
    attrs = extract_attributes(raw, "10's")
    assert attrs.release_type == "prolonged_release"
    assert attrs.dosage_form == "Tablets"
    assert "100mg" in attrs.strengths

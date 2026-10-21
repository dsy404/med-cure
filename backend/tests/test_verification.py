import pytest
from app.services.data_loader import DataLoader
from app.services.verification import VerificationEngine
from app.services.price_comparison import calculate_savings, parse_pack_units
from app.schemas.verification import PriceEvidence
from app.schemas.medicine import VerificationStatus

@pytest.fixture(scope="module")
def data_loader():
    loader = DataLoader()
    loader.load_all()
    return loader

@pytest.fixture(scope="module")
def verifier(data_loader):
    return VerificationEngine(data_loader.rs_benchmarks)

def test_parse_pack_units():
    count, u_type = parse_pack_units("10's")
    assert count == 10.0
    assert u_type == "count"

    count, u_type = parse_pack_units("1 Tablet")
    assert count == 1.0
    assert u_type == "count"

    count, u_type = parse_pack_units("100 ml")
    assert count == 100.0
    assert u_type == "ml"

def test_verified_price_comparison_with_official_benchmark(data_loader, verifier):
    cand = data_loader.get_by_id("GEN-511") # Paracetamol Tablets IP 650 mg (Rs 15.47 / 15's)
    assert cand is not None

    result = verifier.verify(
        query="Dolo 650",
        candidate=cand
    )
    assert result.verification_status == VerificationStatus.VERIFIED_FOR_PRICE_COMPARISON
    assert result.savings.is_eligible is True
    assert result.savings.absolute_saving_inr > 0
    assert result.savings.percentage_saving > 0
    assert result.reference_price_evidence is not None
    assert "Rajya Sabha" in result.reference_price_evidence.effective_or_verified_date

def test_ceiling_price_incomparable_for_patient_savings(data_loader, verifier):
    cand = data_loader.get_by_id("CEIL-1") # Acetylsalicylic acid
    assert cand is not None

    result = verifier.verify(
        query="Aspirin 300mg",
        candidate=cand
    )
    assert result.verification_status == VerificationStatus.INCOMPARABLE_PRICE_BASIS
    assert result.savings.is_eligible is False
    assert "statutory ceiling price" in result.savings.ineligible_reason.lower()

def test_zero_mrp_candidate_rejected(data_loader, verifier):
    zero_prods = [p for p in data_loader.generic_products if p.price.amount_inr == 0.0]
    cand = zero_prods[0]

    result = verifier.verify(
        query=cand.name,
        candidate=cand,
        user_ref_price=50.0
    )
    assert result.verification_status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert result.savings.is_eligible is False

def test_strength_mismatch_needs_clarification(data_loader, verifier):
    cand = data_loader.get_by_id("GEN-511") # 650 mg
    result = verifier.verify(
        query="Paracetamol 500mg",
        candidate=cand
    )
    assert result.verification_status == VerificationStatus.NEEDS_CLARIFICATION
    assert result.savings.is_eligible is False
    strength_check = next(c for c in result.attribute_checks if c.attribute_name == "strength")
    assert strength_check.is_match is False

def test_unspecified_strength_needs_clarification(data_loader, verifier):
    cand = data_loader.get_by_id("GEN-511")
    result = verifier.verify(
        query="Paracetamol", # No strength given
        candidate=cand
    )
    assert result.verification_status == VerificationStatus.NEEDS_CLARIFICATION
    assert result.savings.is_eligible is False
    strength_check = next(c for c in result.attribute_checks if c.attribute_name == "strength")
    assert strength_check.confidence.value == "UNVERIFIED"

def test_savings_calculation_deterministic_math():
    ref = PriceEvidence(
        source_organization="Test Pharmacy",
        source_record_id="REF-1",
        source_file="test",
        price_type="retail_mrp",
        amount_inr=100.0,
        unit_basis="10's",
        effective_or_verified_date="today",
        limitations="test"
    )
    comp = PriceEvidence(
        source_organization="PMBJP",
        source_record_id="GEN-1",
        source_file="test",
        price_type="generic_mrp",
        amount_inr=20.0,
        unit_basis="10's",
        effective_or_verified_date="today",
        limitations="test"
    )
    savings = calculate_savings(ref, comp)
    assert savings.is_eligible is True
    assert savings.absolute_saving_inr == 80.0
    assert savings.percentage_saving == 80.0

def test_savings_negative_difference_transparent():
    ref = PriceEvidence(
        source_organization="Test Pharmacy",
        source_record_id="REF-2",
        source_file="test",
        price_type="retail_mrp",
        amount_inr=10.0,
        unit_basis="10's",
        effective_or_verified_date="today",
        limitations="test"
    )
    comp = PriceEvidence(
        source_organization="PMBJP",
        source_record_id="GEN-2",
        source_file="test",
        price_type="generic_mrp",
        amount_inr=15.0,
        unit_basis="10's",
        effective_or_verified_date="today",
        limitations="test"
    )
    savings = calculate_savings(ref, comp)
    assert savings.is_eligible is True
    assert savings.absolute_saving_inr == -5.0
    assert savings.percentage_saving == -50.0

def test_single_molecule_query_against_combination_candidate_blocked(data_loader, verifier):
    # GEN-1 is Aceclofenac 100mg and Paracetamol 325mg Tablets (Combination Product)
    cand = data_loader.get_by_id("GEN-1")
    assert cand is not None

    result = verifier.verify(
        query="Crocin 325",  # Single-molecule brand query for Paracetamol
        candidate=cand
    )
    # Must NOT be verified for price comparison because candidate has extra NSAID (Aceclofenac)
    assert result.verification_status != VerificationStatus.VERIFIED_FOR_PRICE_COMPARISON
    assert result.verification_status == VerificationStatus.NEEDS_CLARIFICATION
    assert result.savings.is_eligible is False
    ing_check = next(c for c in result.attribute_checks if c.attribute_name == "active_ingredients")
    assert ing_check.is_match is False
    assert "Combination medicine conflict" in ing_check.details


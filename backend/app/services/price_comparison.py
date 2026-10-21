import re
from typing import Tuple, Optional
from ..schemas.verification import SavingsBreakdown, PriceEvidence

def parse_pack_units(unit_str: str) -> Tuple[Optional[float], str]:
    """
    Parses unit size strings such as "10's", "15's", "100 ml", "15 g", "1 Tablet".
    Returns (count, unit_type).
    """
    if not unit_str:
        return None, "unknown"
    
    clean = unit_str.strip().lower()
    # Match "10's" or "14's"
    m_pack = re.match(r"^(\d+)\s*['’]s$", clean)
    if m_pack:
        return float(m_pack.group(1)), "count"

    # Match "1 Tablet", "1 Capsule"
    m_unit = re.match(r"^(\d+(?:\.\d+)?)\s*(tablet|tablets|capsule|capsules|unit|units|bottle|vial|ampoule)$", clean)
    if m_unit:
        return float(m_unit.group(1)), "count"

    # Match volume/weight: e.g. "100 ml", "15 g", "3 ml"
    m_vol = re.match(r"^(\d+(?:\.\d+)?)\s*(ml|g|gm|l|kg)$", clean)
    if m_vol:
        return float(m_vol.group(1)), m_vol.group(2)

    return None, clean

def calculate_savings(
    ref_evidence: PriceEvidence,
    comp_evidence: PriceEvidence
) -> SavingsBreakdown:
    """
    Deterministically computes price differences only when price bases are compatible.
    Rejects incompatible price types (e.g. ceiling price vs retail MRP for patient savings).
    """
    # 1. Price type compatibility check
    if ref_evidence.price_type == "ceiling_price_excluding_taxes":
        return SavingsBreakdown(
            is_eligible=False,
            ineligible_reason=(
                "Statutory ceiling price (DPCO/NPPA) represents an upper legal cap, "
                "not an actual retail purchase quote. Comparing statutory ceiling prices "
                "directly against retail prices is invalid for verified patient savings."
            ),
            normalized_unit_basis=comp_evidence.unit_basis,
            formula_applied="INELIGIBLE_PRICE_TYPE"
        )

    # 2. Check positive amounts
    if ref_evidence.amount_inr <= 0:
        return SavingsBreakdown(
            is_eligible=False,
            ineligible_reason="Reference price is zero or not recorded.",
            normalized_unit_basis=comp_evidence.unit_basis,
            formula_applied="INELIGIBLE_ZERO_REFERENCE"
        )

    if comp_evidence.amount_inr <= 0:
        return SavingsBreakdown(
            is_eligible=False,
            ineligible_reason="Catalogue medicine listed price is zero or unusable for price comparison.",
            normalized_unit_basis=comp_evidence.unit_basis,
            formula_applied="INELIGIBLE_ZERO_COMPARISON"
        )

    # 3. Unit basis normalization
    ref_count, ref_type = parse_pack_units(ref_evidence.unit_basis)
    comp_count, comp_type = parse_pack_units(comp_evidence.unit_basis)

    assumptions = []

    if ref_type != comp_type and ref_type != "unknown" and comp_type != "unknown":
        return SavingsBreakdown(
            is_eligible=False,
            ineligible_reason=f"Incompatible unit types: reference is '{ref_evidence.unit_basis}' ({ref_type}) vs comparison is '{comp_evidence.unit_basis}' ({comp_type}).",
            normalized_unit_basis="incompatible",
            formula_applied="INCOMPATIBLE_UNIT_TYPE"
        )

    # If both have countable units (e.g. 10 tablets vs 15 tablets)
    if ref_count and comp_count and ref_count > 0 and comp_count > 0:
        ref_per_unit = ref_evidence.amount_inr / ref_count
        comp_per_unit = comp_evidence.amount_inr / comp_count

        # Normalize to standard 10 units (standard Indian blister pack size)
        norm_ref = round(ref_per_unit * 10, 2)
        norm_comp = round(comp_per_unit * 10, 2)
        norm_basis = "10 units (standardized pack)"

        assumptions.append(
            f"Normalized reference from {ref_evidence.unit_basis} (₹{ref_evidence.amount_inr}) to ₹{ref_per_unit:.2f}/unit."
        )
        assumptions.append(
            f"Normalized comparison from {comp_evidence.unit_basis} (₹{comp_evidence.amount_inr}) to ₹{comp_per_unit:.2f}/unit."
        )
        assumptions.append("Compared on a standardized 10-unit basis.")

        abs_diff = round(norm_ref - norm_comp, 2)
        pct_diff = round((abs_diff / norm_ref) * 100, 1)

        formula = f"({norm_ref} - {norm_comp}) = ₹{abs_diff} ({pct_diff}%)"

        return SavingsBreakdown(
            is_eligible=True,
            ineligible_reason=None,
            reference_price_inr=norm_ref,
            comparison_price_inr=norm_comp,
            normalized_unit_basis=norm_basis,
            absolute_saving_inr=abs_diff,
            percentage_saving=pct_diff,
            formula_applied=formula,
            assumptions=assumptions
        )

    # If counts cannot be parsed or are identical string units (e.g. both "10's")
    if ref_evidence.unit_basis.strip().lower() == comp_evidence.unit_basis.strip().lower():
        abs_diff = round(ref_evidence.amount_inr - comp_evidence.amount_inr, 2)
        pct_diff = round((abs_diff / ref_evidence.amount_inr) * 100, 1)
        formula = f"({ref_evidence.amount_inr} - {comp_evidence.amount_inr}) = ₹{abs_diff} ({pct_diff}%)"
        return SavingsBreakdown(
            is_eligible=True,
            ineligible_reason=None,
            reference_price_inr=ref_evidence.amount_inr,
            comparison_price_inr=comp_evidence.amount_inr,
            normalized_unit_basis=comp_evidence.unit_basis,
            absolute_saving_inr=abs_diff,
            percentage_saving=pct_diff,
            formula_applied=formula,
            assumptions=["Direct pack comparison without quantity conversion."]
        )

    return SavingsBreakdown(
        is_eligible=False,
        ineligible_reason=f"Could not reliably normalize unit basis '{ref_evidence.unit_basis}' vs '{comp_evidence.unit_basis}'.",
        normalized_unit_basis="unresolved",
        formula_applied="UNRESOLVED_UNIT_NORMALIZATION"
    )

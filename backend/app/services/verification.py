import datetime
from typing import Optional, List, Dict
from ..schemas.medicine import MedicineProduct, VerificationStatus
from ..schemas.verification import (
    VerificationResult,
    AttributeVerificationItem,
    MatchConfidence,
    PriceEvidence,
    SavingsBreakdown
)
from .normalizer import extract_attributes, normalize_text
from .brand_aliases import lookup_brand_alias
from .price_comparison import calculate_savings

class VerificationEngine:
    def __init__(self, rs_benchmarks: Optional[List[Dict]] = None):
        self.rs_benchmarks = rs_benchmarks or []
        self._benchmark_index: Dict[str, Dict] = {}
        for b in self.rs_benchmarks:
            name_norm = normalize_text(str(b.get("Name of Medicine", "")))
            self._benchmark_index[name_norm] = b

    def find_official_benchmark(self, candidate_name: str) -> Optional[Dict]:
        """
        Matches candidate against Rajya Sabha official government branded price benchmark.
        """
        c_norm = normalize_text(candidate_name)
        for b_name, b_data in self._benchmark_index.items():
            # Check key token overlaps e.g. "paracetamol" & "650", "atorvastatin" & "10"
            b_tokens = set(b_name.split())
            c_tokens = set(c_norm.split())
            if b_tokens.issubset(c_tokens) or b_name in c_norm:
                return b_data
        return None

    def verify(
        self,
        query: str,
        candidate: MedicineProduct,
        user_ref_price: Optional[float] = None,
        user_ref_unit: Optional[str] = None,
        reference_brand: Optional[str] = None
    ) -> VerificationResult:
        query_clean = query.strip()
        query_attrs = extract_attributes(query_clean)
        cand_attrs = candidate.attributes

        attribute_checks: List[AttributeVerificationItem] = []

        # 1. Check Active Ingredients
        alias = lookup_brand_alias(query_clean)
        if alias:
            ref_ingredients = [alias.active_molecule]
            target_ref_molecule = alias.active_molecule
        elif query_attrs.ingredients:
            ref_ingredients = query_attrs.ingredients
            target_ref_molecule = " ".join(query_attrs.ingredients)
        else:
            ref_ingredients = [query_clean]
            target_ref_molecule = query_clean
        
        # Check ingredient overlap
        ref_ing_norm = [normalize_text(i) for i in ref_ingredients]
        cand_ing_norm = [normalize_text(i) for i in cand_attrs.ingredients]

        ing_match = False
        ing_conf = MatchConfidence.MISMATCH
        ing_details = ""

        # Determine matched and unmatched ingredients
        matched_cand_ings = [
            c for c, cn in zip(cand_attrs.ingredients, cand_ing_norm)
            if any(rn in cn or cn in rn for rn in ref_ing_norm)
        ]
        extra_cand_ings = [
            c for c in cand_attrs.ingredients if c not in matched_cand_ings
        ]
        missing_ref_ings = [
            r for r, rn in zip(ref_ingredients, ref_ing_norm)
            if not any(rn in cn or cn in rn for cn in cand_ing_norm)
        ]

        if not missing_ref_ings and not extra_cand_ings and matched_cand_ings:
            # Complete bilateral active ingredient equivalence
            ing_match = True
            ing_conf = MatchConfidence.EXACT
            ing_details = f"Active ingredients verified: candidate matches {', '.join(cand_attrs.ingredients)}."
        elif extra_cand_ings and matched_cand_ings:
            # Candidate contains additional active drug molecules (Combination Product)
            ing_match = False
            ing_conf = MatchConfidence.MISMATCH
            ing_details = (
                f"Combination medicine conflict: candidate contains additional active molecule(s) "
                f"({', '.join(extra_cand_ings)}) not present in prescribed reference '{target_ref_molecule}'. "
                f"Combination products cannot be substituted for single-molecule prescriptions."
            )
        elif missing_ref_ings:
            ing_match = False
            ing_conf = MatchConfidence.MISMATCH
            ing_details = (
                f"Active ingredient deficit: candidate lacks required molecule(s) ({', '.join(missing_ref_ings)}). "
                f"Candidate formulation has: {', '.join(cand_attrs.ingredients)}."
            )
        else:
            ing_match = False
            ing_conf = MatchConfidence.MISMATCH
            ing_details = f"Active ingredient discrepancy: query specified '{target_ref_molecule}', candidate has '{', '.join(cand_attrs.ingredients)}'."

        attribute_checks.append(AttributeVerificationItem(
            attribute_name="active_ingredients",
            reference_value=target_ref_molecule,
            candidate_value=", ".join(cand_attrs.ingredients) if cand_attrs.ingredients else candidate.name,
            is_match=ing_match,
            confidence=ing_conf,
            details=ing_details
        ))

        # 2. Check Strength
        ref_strengths = query_attrs.strengths or ([alias.typical_strength] if alias and alias.typical_strength else [])
        cand_strengths = cand_attrs.strengths

        strength_match = False
        strength_conf = MatchConfidence.UNVERIFIED
        strength_details = ""

        if not ref_strengths:
            strength_conf = MatchConfidence.UNVERIFIED
            strength_details = f"Query did not state strength. Candidate documents {', '.join(cand_strengths) if cand_strengths else 'unknown'}."
        elif any(rs.lower() in [cs.lower() for cs in cand_strengths] for rs in ref_strengths):
            strength_match = True
            strength_conf = MatchConfidence.EXACT
            strength_details = f"Exact strength match: {', '.join(ref_strengths)}."
        else:
            strength_conf = MatchConfidence.MISMATCH
            strength_details = f"Strength mismatch: query specified {', '.join(ref_strengths)}, candidate is {', '.join(cand_strengths)}."

        attribute_checks.append(AttributeVerificationItem(
            attribute_name="strength",
            reference_value=", ".join(ref_strengths) if ref_strengths else "unspecified",
            candidate_value=", ".join(cand_strengths) if cand_strengths else "unspecified",
            is_match=strength_match,
            confidence=strength_conf,
            details=strength_details
        ))

        # 3. Check Dosage Form
        form_match = True
        form_conf = MatchConfidence.COMPATIBLE
        form_details = f"Candidate dosage form: {cand_attrs.dosage_form or 'Not specified'}."

        if query_attrs.dosage_form and cand_attrs.dosage_form:
            if query_attrs.dosage_form.lower() in cand_attrs.dosage_form.lower():
                form_match = True
                form_conf = MatchConfidence.EXACT
                form_details = f"Dosage form matches: {cand_attrs.dosage_form}."
            else:
                form_match = False
                form_conf = MatchConfidence.MISMATCH
                form_details = f"Dosage form mismatch: query specified '{query_attrs.dosage_form}', candidate is '{cand_attrs.dosage_form}'."

        attribute_checks.append(AttributeVerificationItem(
            attribute_name="dosage_form",
            reference_value=query_attrs.dosage_form or "unspecified",
            candidate_value=cand_attrs.dosage_form or "unspecified",
            is_match=form_match,
            confidence=form_conf,
            details=form_details
        ))

        # 4. Check Release Characteristics
        release_match = True
        release_conf = MatchConfidence.COMPATIBLE
        release_details = "Standard release profile."

        if cand_attrs.release_type:
            release_details = f"Candidate requires {cand_attrs.release_type.replace('_', ' ').capitalize()}."
            if query_attrs.release_type and query_attrs.release_type != cand_attrs.release_type:
                release_match = False
                release_conf = MatchConfidence.MISMATCH
                release_details = f"Release profile conflict: {query_attrs.release_type} vs {cand_attrs.release_type}."

        attribute_checks.append(AttributeVerificationItem(
            attribute_name="release_characteristics",
            reference_value=query_attrs.release_type or "standard",
            candidate_value=cand_attrs.release_type or "standard",
            is_match=release_match,
            confidence=release_conf,
            details=release_details
        ))

        # 5. Price Evidence Assembly
        comp_price_evidence = PriceEvidence(
            source_organization=("Jan Aushadhi (PMBJP)" if candidate.catalogue_type == "generic_product" else "NPPA (DPCO 2013)"),
            source_record_id=candidate.product_id,
            source_file=candidate.source_file,
            price_type=candidate.price.price_type,
            amount_inr=candidate.price.amount_inr,
            unit_basis=candidate.price.unit_basis,
            effective_or_verified_date=candidate.source_verification_status,
            limitations=candidate.price.disclaimer
        )

        ref_price_evidence: Optional[PriceEvidence] = None

        # Look up official government benchmark or user-reported price
        gov_benchmark = self.find_official_benchmark(candidate.name)
        
        if user_ref_price is not None and user_ref_price > 0:
            ref_price_evidence = PriceEvidence(
                source_organization="User Prescribed / Purchased Quote",
                source_record_id="USER-ENTRY",
                source_file="User Input",
                price_type="user_reported_retail_price",
                amount_inr=float(user_ref_price),
                unit_basis=user_ref_unit or candidate.unit_size,
                effective_or_verified_date="Current user session",
                limitations="Self-reported price entry; not independently verified against pharmacy invoice."
            )
        elif gov_benchmark:
            try:
                avg_branded_mrp = float(gov_benchmark.get("Avg. MRP of branded Medicines (in Rs.)", 0))
                ref_price_evidence = PriceEvidence(
                    source_organization="Ministry of Chemicals & Fertilizers (Govt. of India)",
                    source_record_id=f"RS-Q-{gov_benchmark.get('Sl. No.')}",
                    source_file="RS_Session_255_AU_1784_B.csv",
                    price_type="government_reported_average_branded_mrp",
                    amount_inr=avg_branded_mrp,
                    unit_basis=candidate.unit_size,
                    effective_or_verified_date="Rajya Sabha Session 255 Annexure 1784-B",
                    limitations="Official government surveyed average MRP for leading branded market leaders."
                )
            except (ValueError, TypeError):
                ref_price_evidence = None

        # Determine Verification Status
        savings: SavingsBreakdown

        if candidate.catalogue_type == "ceiling_price_reference":
            status = VerificationStatus.INCOMPARABLE_PRICE_BASIS
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason=(
                    "The matched record is a government statutory ceiling price cap (DPCO/NPPA), "
                    "not an actual retail pharmacy selling price. Comparing a statutory ceiling cap "
                    "against retail MRP is rejected to prevent misleading patient savings claims."
                ),
                normalized_unit_basis=candidate.unit_size,
                formula_applied="CEILING_PRICE_NOT_RETAIL_QUOTE"
            )
            summary = "Record is a regulatory ceiling price cap, not a retail product quote. Price comparison cannot be established."

        elif not candidate.price.usable_for_comparison or candidate.price.amount_inr <= 0:
            status = VerificationStatus.INSUFFICIENT_EVIDENCE
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason="Candidate record has zero or unlisted MRP in the Jan Aushadhi catalogue.",
                normalized_unit_basis=candidate.unit_size,
                formula_applied="UNLISTED_CATALOGUE_PRICE"
            )
            summary = "Catalogue record price is listed as zero or unusable for verified comparison."

        elif not ing_match:
            status = VerificationStatus.NEEDS_CLARIFICATION
            reason = (
                f"Combination medicine contains extra active ingredient(s) ({', '.join(extra_cand_ings)}). Incompatible with single-molecule prescription."
                if extra_cand_ings else "Active ingredient does not match query."
            )
            formula = "COMBINATION_DRUG_CONFLICT" if extra_cand_ings else "INGREDIENT_MISMATCH"
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason=reason,
                normalized_unit_basis=candidate.unit_size,
                formula_applied=formula
            )
            summary = ing_details


        elif not strength_match and ref_strengths:
            status = VerificationStatus.NEEDS_CLARIFICATION
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason="Medicine strength does not match query.",
                normalized_unit_basis=candidate.unit_size,
                formula_applied="STRENGTH_MISMATCH"
            )
            summary = f"Dosage strength mismatch: query was {', '.join(ref_strengths)} but catalogue is {', '.join(cand_strengths)}."

        elif strength_conf == MatchConfidence.UNVERIFIED:
            status = VerificationStatus.NEEDS_CLARIFICATION
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason="Dosage strength was omitted in query. Must clarify exact strength before comparison.",
                normalized_unit_basis=candidate.unit_size,
                formula_applied="UNSPECIFIED_QUERY_STRENGTH"
            )
            summary = "Query did not state prescribed strength. Please clarify strength before calculating savings."

        elif not form_match or not release_match:
            status = VerificationStatus.NEEDS_CLARIFICATION
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason="Dosage form or release profile mismatch.",
                normalized_unit_basis=candidate.unit_size,
                formula_applied="FORMULATION_MISMATCH"
            )
            summary = "Pharmaceutical formulation or release characteristics differ. Substitution requires physician confirmation."

        elif ref_price_evidence is None:
            status = VerificationStatus.INSUFFICIENT_EVIDENCE
            savings = SavingsBreakdown(
                is_eligible=False,
                ineligible_reason="No verified branded reference price available for this molecule/strength.",
                normalized_unit_basis=candidate.unit_size,
                formula_applied="NO_REFERENCE_PRICE_DATA"
            )
            summary = "Catalogue product verified, but reference branded retail price is unrecorded. Provide your pharmacy price to calculate savings."

        else:
            # Genuine comparable evidence exists!
            savings = calculate_savings(ref_price_evidence, comp_price_evidence)
            if savings.is_eligible:
                status = VerificationStatus.VERIFIED_FOR_PRICE_COMPARISON
                summary = (
                    f"Verified comparison: Generic {candidate.name} (₹{savings.comparison_price_inr} per {savings.normalized_unit_basis}) "
                    f"vs Reference (₹{savings.reference_price_inr}). Potential difference: ₹{savings.absolute_saving_inr} ({savings.percentage_saving}%)."
                )
            else:
                status = VerificationStatus.INCOMPARABLE_PRICE_BASIS
                summary = f"Price comparison ineligible: {savings.ineligible_reason}"

        return VerificationResult(
            verification_status=status,
            query=query_clean,
            candidate_id=candidate.product_id,
            candidate_name=candidate.name,
            candidate_catalogue_type=candidate.catalogue_type,
            attribute_checks=attribute_checks,
            reference_price_evidence=ref_price_evidence,
            comparison_price_evidence=comp_price_evidence,
            savings=savings,
            plain_language_summary=summary,
            verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

import time
import re
from typing import List, Optional, Dict, Set
from rapidfuzz import fuzz

from ..schemas.medicine import (
    MedicineProduct,
    SearchCandidate,
    SearchResponse,
    RetrievalMethod,
)
from .data_loader import DataLoader
from .normalizer import normalize_text, extract_attributes, STRENGTH_REGEX, DOSAGE_FORMS
from .brand_aliases import lookup_brand_alias, BRAND_ALIASES

class MedicineSearchEngine:
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self._indexed = False
        self._generic_index: List[Dict] = []
        self._ceiling_index: List[Dict] = []
        self._name_to_product: Dict[str, MedicineProduct] = {}

    def ensure_indexed(self) -> None:
        if self._indexed:
            return
        if not self.data_loader.loaded:
            self.data_loader.load_all()

        for p in self.data_loader.generic_products:
            norm = normalize_text(p.name)
            self._generic_index.append({
                "product": p,
                "norm_name": norm,
                "tokens": set(norm.split()),
                "strengths": [s.lower() for s in p.attributes.strengths],
                "dosage_form": (p.attributes.dosage_form.lower() if p.attributes.dosage_form else ""),
                "catalogue_type": "generic_product",
            })
            self._name_to_product[p.name.strip().lower()] = p

        for p in self.data_loader.ceiling_products:
            norm = normalize_text(p.name)
            self._ceiling_index.append({
                "product": p,
                "norm_name": norm,
                "tokens": set(norm.split()),
                "strengths": [s.lower() for s in p.attributes.strengths],
                "dosage_form": (p.attributes.dosage_form.lower() if p.attributes.dosage_form else ""),
                "catalogue_type": "ceiling_price_reference",
            })
            self._name_to_product[p.name.strip().lower()] = p

        self._indexed = True

    def search(
        self,
        query: str,
        limit: int = 10,
        include_ceiling_prices: bool = True
    ) -> SearchResponse:
        start_time = time.perf_counter()
        self.ensure_indexed()

        cleaned_raw = query.strip()
        if not cleaned_raw:
            return SearchResponse(
                query=query,
                normalized_query="",
                total_candidates=0,
                retrieval_strategy_applied="NONE",
                candidates=[],
                message="Search query is empty. Please enter a medicine name, active ingredient, or brand.",
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2)
            )

        norm_query = normalize_text(cleaned_raw)
        query_tokens = set(norm_query.split())
        query_attrs = extract_attributes(cleaned_raw)
        query_strengths = [s.lower() for s in query_attrs.strengths]
        query_form = query_attrs.dosage_form.lower() if query_attrs.dosage_form else None

        candidates_map: Dict[str, SearchCandidate] = {}
        applied_strategies: List[str] = []

        pool = self._generic_index
        if include_ceiling_prices:
            pool = self._generic_index + self._ceiling_index

        # Stage 1: Exact match on full product name
        for item in pool:
            p = item["product"]
            if p.name.strip().lower() == cleaned_raw.lower():
                candidates_map[p.product_id] = SearchCandidate(
                    product=p,
                    retrieval_method=RetrievalMethod.EXACT_MATCH,
                    match_score=100.0,
                    matched_term=p.name,
                    notes="Exact name match in official catalogue."
                )
        if candidates_map:
            applied_strategies.append("EXACT_MATCH")

        # Stage 2: Verified Brand Alias Lookup
        alias = lookup_brand_alias(cleaned_raw)
        if alias:
            applied_strategies.append("ALIAS_MATCH")
            # Search pool using alias target search term and active molecule
            alias_target_norm = normalize_text(alias.target_search_term)
            alias_mol_norm = normalize_text(alias.active_molecule)
            alias_strength = alias.typical_strength.lower() if alias.typical_strength else None

            for item in pool:
                p = item["product"]
                if p.product_id in candidates_map:
                    continue
                item_norm = item["norm_name"]
                # Match if molecule or target term is contained
                score = 0.0
                if alias_target_norm in item_norm:
                    score = 96.0
                elif alias_mol_norm in item_norm:
                    score = 92.0
                    # Boost if strength matches
                    if alias_strength and alias_strength in item["strengths"]:
                        score += 3.0

                if score >= 90.0:
                    candidates_map[p.product_id] = SearchCandidate(
                        product=p,
                        retrieval_method=RetrievalMethod.ALIAS_MATCH,
                        match_score=score,
                        matched_term=alias.brand_name,
                        notes=f"Retrieved via verified brand mapping: '{alias.brand_name}' -> '{alias.active_molecule}' ({alias.provenance})"
                    )

        # Stage 3: Normalized-name match
        for item in pool:
            p = item["product"]
            if p.product_id in candidates_map:
                continue
            if item["norm_name"] == norm_query:
                candidates_map[p.product_id] = SearchCandidate(
                    product=p,
                    retrieval_method=RetrievalMethod.NORMALIZED_MATCH,
                    match_score=95.0,
                    matched_term=p.name,
                    notes="Normalized text match (case/punctuation normalized)."
                )
        if any(c.retrieval_method == RetrievalMethod.NORMALIZED_MATCH for c in candidates_map.values()):
            applied_strategies.append("NORMALIZED_MATCH")

        # Stage 4: Partial-name / Token subset retrieval
        # If query has at least 3 chars
        if len(norm_query) >= 3:
            for item in pool:
                p = item["product"]
                if p.product_id in candidates_map:
                    continue
                item_norm = item["norm_name"]
                item_tokens = item["tokens"]

                # Substring containment
                if norm_query in item_norm:
                    # Score based on length ratio
                    ratio = len(norm_query) / len(item_norm)
                    score = round(85.0 + (ratio * 10.0), 1)
                    candidates_map[p.product_id] = SearchCandidate(
                        product=p,
                        retrieval_method=RetrievalMethod.PARTIAL_MATCH,
                        match_score=score,
                        matched_term=norm_query,
                        notes="Substring match in product formulation."
                    )
                elif query_tokens and query_tokens.issubset(item_tokens):
                    # All query tokens contained
                    candidates_map[p.product_id] = SearchCandidate(
                        product=p,
                        retrieval_method=RetrievalMethod.PARTIAL_MATCH,
                        match_score=88.0,
                        matched_term=" ".join(query_tokens),
                        notes="Token containment match in product formulation."
                    )
        if any(c.retrieval_method == RetrievalMethod.PARTIAL_MATCH for c in candidates_map.values()):
            applied_strategies.append("PARTIAL_MATCH")

        # Stage 5: RapidFuzz typo-tolerant fuzzy matching
        # Only run fuzzy if we have fewer than limit candidates or if user specifically misspelled
        fuzzy_candidates = []
        for item in pool:
            p = item["product"]
            if p.product_id in candidates_map:
                continue
            item_norm = item["norm_name"]

            # Token sort ratio handles word order variations
            sort_ratio = fuzz.token_sort_ratio(norm_query, item_norm)
            partial_ratio = fuzz.partial_ratio(norm_query, item_norm)
            
            # Combine score prioritizing token sort ratio
            fuzzy_score = max(sort_ratio, partial_ratio * 0.85)
            
            # Only accept high textual similarity (honest threshold)
            if fuzzy_score >= 68.0:
                fuzzy_candidates.append((fuzzy_score, item, p))

        for fuzzy_score, item, p in fuzzy_candidates:
            if p.product_id not in candidates_map:
                candidates_map[p.product_id] = SearchCandidate(
                    product=p,
                    retrieval_method=RetrievalMethod.FUZZY_MATCH,
                    match_score=round(fuzzy_score, 1),
                    matched_term=p.name,
                    notes=f"Typo-tolerant textual similarity ({round(fuzzy_score, 1)}%). Does not indicate clinical equivalence."
                )
        if any(c.retrieval_method == RetrievalMethod.FUZZY_MATCH for c in candidates_map.values()):
            applied_strategies.append("FUZZY_MATCH")

        # Stage 6: Attribute-aware ranking
        target_ing_count = 1 if alias else (len(query_attrs.ingredients) if query_attrs.ingredients else None)
        target_mol_norm = normalize_text(alias.active_molecule) if alias else (normalize_text(query_attrs.ingredients[0]) if query_attrs.ingredients else None)

        def ranking_key(cand: SearchCandidate):
            score = cand.match_score
            prod = cand.product
            cand_ings = prod.attributes.ingredients
            cand_ing_count = len(cand_ings)

            # Bonus for single-ingredient match when searching for single-ingredient/brand
            if target_ing_count == 1:
                if cand_ing_count == 1:
                    score += 15.0  # Strong preference for pure single-molecule formulation
                else:
                    score -= 4.0   # Combination products ranked below pure single molecules
            elif target_ing_count and target_ing_count > 1:
                if cand_ing_count == target_ing_count:
                    score += 10.0

            # Bonus for exact ingredient name match
            if target_mol_norm and any(target_mol_norm == normalize_text(ing) for ing in cand_ings):
                score += 5.0

            # Bonus for strength match if query explicitly stated strength
            if query_strengths and any(qs in [s.lower() for s in prod.attributes.strengths] for qs in query_strengths):
                score += 8.0
            elif alias and alias.typical_strength and any(alias.typical_strength.lower() in s.lower() for s in prod.attributes.strengths):
                score += 6.0

            # Bonus for dosage form match if query specified dosage form
            if query_form and prod.attributes.dosage_form and prod.attributes.dosage_form.lower() == query_form:
                score += 3.0

            # Small preference for products usable for price comparison
            if prod.price.usable_for_comparison:
                score += 2.0

            # Small preference for generic products over ceiling references
            if prod.catalogue_type == "generic_product":
                score += 1.0

            return score

        # Enrich candidate notes for combination medicines when query was for a single molecule
        for cand in candidates_map.values():
            prod = cand.product
            if target_ing_count == 1 and len(prod.attributes.ingredients) > 1:
                target_name = alias.active_molecule if alias else query_attrs.ingredients[0]
                cand.notes = (
                    f"Combination medicine ({', '.join(prod.attributes.ingredients)}). "
                    f"Contains {target_name}, but is NOT clinically interchangeable with single-molecule {target_name}."
                )

        sorted_candidates = sorted(candidates_map.values(), key=ranking_key, reverse=True)
        final_candidates = sorted_candidates[:limit]

        exec_time = round((time.perf_counter() - start_time) * 1000, 2)
        strat_str = " + ".join(applied_strategies) if applied_strategies else "NONE"

        if not final_candidates:
            msg = f"No catalogue match found for '{cleaned_raw}'. Please check spelling or search by active molecule (e.g. Paracetamol, Metformin)."
        else:
            msg = f"Found {len(final_candidates)} catalogue candidate(s) for '{cleaned_raw}'."

        return SearchResponse(
            query=cleaned_raw,
            normalized_query=norm_query,
            total_candidates=len(final_candidates),
            retrieval_strategy_applied=strat_str,
            candidates=final_candidates,
            message=msg,
            execution_time_ms=exec_time
        )


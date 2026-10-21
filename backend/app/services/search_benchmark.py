import time
from typing import List, Dict, Any
from pydantic import BaseModel

from .data_loader import DataLoader
from .medicine_search import MedicineSearchEngine
from .verification import VerificationEngine
from .gemma_interpreter import GemmaInterpreterService
from ..schemas.medicine import RetrievalMethod, VerificationStatus

BENCHMARK_CASES = [
    {
        "query": "Aceclofenac Tablets IP 100 mg",
        "expected_product_id": "GEN-2",
        "category": "exact_match",
        "should_abstain": False,
        "description": "Full exact product name"
    },
    {
        "query": "paracetmol 650",
        "expected_molecule": "paracetamol",
        "category": "spelling_typo",
        "should_abstain": False,
        "description": "Common spelling mistake in active ingredient"
    },
    {
        "query": "Dolo 650",
        "expected_product_id": "GEN-511",
        "category": "brand_alias",
        "should_abstain": False,
        "description": "Leading Indian brand name to generic equivalence"
    },
    {
        "query": "Augmentin 625",
        "expected_molecule": "amoxycillin",
        "category": "brand_combination",
        "should_abstain": False,
        "description": "Antibiotic combination brand query"
    },
    {
        "query": "Paracetamol",
        "expected_molecule": "paracetamol",
        "category": "ambiguous_missing_strength",
        "should_abstain": False, # Returns candidates, but verification MUST require clarification!
        "description": "Molecule name without strength"
    },
    {
        "query": "Metformin 500",
        "expected_molecule": "metformin",
        "category": "partial_query",
        "should_abstain": False,
        "description": "Partial name with strength"
    },
    {
        "query": "Xylopharmazine 999mg",
        "expected_product_id": None,
        "category": "unknown_nonsense",
        "should_abstain": True,
        "description": "Non-existent medicine query (must abstain)"
    },
    {
        "query": "Zolpidem 10000mg Fake",
        "expected_product_id": None,
        "category": "toxic_out_of_catalogue",
        "should_abstain": True,
        "description": "Dangerous/fabricated strength and unknown item"
    }
]

class BenchmarkReport(BaseModel):
    total_test_cases: int
    ollama_status: Dict[str, Any]
    mode_a_exact: Dict[str, Any]
    mode_b_fuzzy_deterministic: Dict[str, Any]
    mode_c_gemma_assisted: Dict[str, Any]
    comparison_summary: str
    detailed_results: List[Dict[str, Any]]

class SearchBenchmarkRunner:
    def __init__(
        self,
        loader: DataLoader,
        engine: MedicineSearchEngine,
        verifier: VerificationEngine,
        gemma: GemmaInterpreterService
    ):
        self.loader = loader
        self.engine = engine
        self.verifier = verifier
        self.gemma = gemma

    def run_benchmark(self) -> BenchmarkReport:
        ollama_status = self.gemma.check_ollama_status()
        details = []

        stats_a = {"top1_correct": 0, "top3_recall": 0, "correct_abstentions": 0, "total_latency_ms": 0.0}
        stats_b = {"top1_correct": 0, "top3_recall": 0, "correct_abstentions": 0, "total_latency_ms": 0.0}
        stats_c = {"top1_correct": 0, "top3_recall": 0, "correct_abstentions": 0, "total_latency_ms": 0.0}

        n = len(BENCHMARK_CASES)

        for case in BENCHMARK_CASES:
            q = case["query"]
            exp_id = case.get("expected_product_id")
            exp_mol = case.get("expected_molecule")
            should_abstain = case["should_abstain"]

            # Mode A: Exact string match only
            t0 = time.perf_counter()
            exact_matches = [p for p in self.loader.generic_products if p.name.strip().lower() == q.strip().lower()]
            lat_a = (time.perf_counter() - t0) * 1000
            stats_a["total_latency_ms"] += lat_a
            
            mode_a_hit = False
            if should_abstain:
                if len(exact_matches) == 0:
                    stats_a["correct_abstentions"] += 1
            else:
                if exact_matches:
                    p = exact_matches[0]
                    if (exp_id and p.product_id == exp_id) or (exp_mol and exp_mol in p.name.lower()):
                        stats_a["top1_correct"] += 1
                        stats_a["top3_recall"] += 1
                        mode_a_hit = True

            # Mode B: Fuzzy Search + Deterministic Verification
            t0 = time.perf_counter()
            res_b = self.engine.search(q, limit=5)
            lat_b = (time.perf_counter() - t0) * 1000
            stats_b["total_latency_ms"] += lat_b

            mode_b_hit = False
            if should_abstain:
                if res_b.total_candidates == 0:
                    stats_b["correct_abstentions"] += 1
                else:
                    # Deterministic verification check prevents false verified comparison
                    v_res = self.verifier.verify(q, res_b.candidates[0].product)
                    if v_res.verification_status != VerificationStatus.VERIFIED_FOR_PRICE_COMPARISON:
                        stats_b["correct_abstentions"] += 1
            else:
                if res_b.candidates:
                    top1 = res_b.candidates[0].product
                    if (exp_id and top1.product_id == exp_id) or (exp_mol and exp_mol in top1.name.lower()):
                        stats_b["top1_correct"] += 1
                        mode_b_hit = True
                    # Check top 3
                    top3 = res_b.candidates[:3]
                    if any((exp_id and c.product.product_id == exp_id) or (exp_mol and exp_mol in c.product.name.lower()) for c in top3):
                        stats_b["top3_recall"] += 1

            # Mode C: Gemma-assisted interpretation + Deterministic Retrieval
            t0 = time.perf_counter()
            ai_interp = self.gemma.interpret_query(q)
            # Use interpreted name if provided, else original query
            search_term = ai_interp.interpreted_name or (ai_interp.possible_names[0] if ai_interp.possible_names else q)
            res_c = self.engine.search(search_term, limit=5)
            lat_c = (time.perf_counter() - t0) * 1000
            stats_c["total_latency_ms"] += lat_c

            mode_c_hit = False
            if should_abstain:
                if res_c.total_candidates == 0 or ai_interp.needs_clarification:
                    stats_c["correct_abstentions"] += 1
                else:
                    v_res = self.verifier.verify(q, res_c.candidates[0].product)
                    if v_res.verification_status != VerificationStatus.VERIFIED_FOR_PRICE_COMPARISON:
                        stats_c["correct_abstentions"] += 1
            else:
                if res_c.candidates:
                    top1 = res_c.candidates[0].product
                    if (exp_id and top1.product_id == exp_id) or (exp_mol and exp_mol in top1.name.lower()):
                        stats_c["top1_correct"] += 1
                        mode_c_hit = True
                    top3 = res_c.candidates[:3]
                    if any((exp_id and c.product.product_id == exp_id) or (exp_mol and exp_mol in c.product.name.lower()) for c in top3):
                        stats_c["top3_recall"] += 1

            details.append({
                "case": case,
                "mode_a_hit": mode_a_hit,
                "mode_b_hit": mode_b_hit,
                "mode_c_hit": mode_c_hit,
                "gemma_available": ai_interp.is_available,
                "latency_a_ms": round(lat_a, 2),
                "latency_b_ms": round(lat_b, 2),
                "latency_c_ms": round(lat_c, 2),
            })

        summary_msg = (
            f"Benchmark on {n} clinical & adversarial test cases: "
            f"Mode A (Exact) Top-1: {stats_a['top1_correct']}/{n - 2}, Latency: {stats_a['total_latency_ms']/n:.1f}ms. "
            f"Mode B (Fuzzy+Deterministic) Top-1: {stats_b['top1_correct']}/{n - 2}, Recall: {stats_b['top3_recall']}/{n - 2}, Latency: {stats_b['total_latency_ms']/n:.1f}ms. "
            f"Mode C (Gemma+Deterministic) Top-1: {stats_c['top1_correct']}/{n - 2}, Recall: {stats_c['top3_recall']}/{n - 2}, Latency: {stats_c['total_latency_ms']/n:.1f}ms."
        )

        return BenchmarkReport(
            total_test_cases=n,
            ollama_status=ollama_status,
            mode_a_exact={
                "top1_accuracy": round((stats_a["top1_correct"] / (n - 2)) * 100, 1),
                "top3_recall": round((stats_a["top3_recall"] / (n - 2)) * 100, 1),
                "correct_abstention_rate": round((stats_a["correct_abstentions"] / 2) * 100, 1),
                "avg_latency_ms": round(stats_a["total_latency_ms"] / n, 2)
            },
            mode_b_fuzzy_deterministic={
                "top1_accuracy": round((stats_b["top1_correct"] / (n - 2)) * 100, 1),
                "top3_recall": round((stats_b["top3_recall"] / (n - 2)) * 100, 1),
                "correct_abstention_rate": round((stats_b["correct_abstentions"] / 2) * 100, 1),
                "avg_latency_ms": round(stats_b["total_latency_ms"] / n, 2)
            },
            mode_c_gemma_assisted={
                "top1_accuracy": round((stats_c["top1_correct"] / (n - 2)) * 100, 1),
                "top3_recall": round((stats_c["top3_recall"] / (n - 2)) * 100, 1),
                "correct_abstention_rate": round((stats_c["correct_abstentions"] / 2) * 100, 1),
                "avg_latency_ms": round(stats_c["total_latency_ms"] / n, 2),
                "model_status": ollama_status["status_message"]
            },
            comparison_summary=summary_msg,
            detailed_results=details
        )

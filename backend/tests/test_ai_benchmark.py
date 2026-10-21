import pytest
from app.services.data_loader import DataLoader
from app.services.medicine_search import MedicineSearchEngine
from app.services.verification import VerificationEngine
from app.services.gemma_interpreter import GemmaInterpreterService
from app.services.search_benchmark import SearchBenchmarkRunner

@pytest.fixture(scope="module")
def benchmark_suite():
    loader = DataLoader()
    loader.load_all()
    engine = MedicineSearchEngine(loader)
    engine.ensure_indexed()
    verifier = VerificationEngine(loader.rs_benchmarks)
    gemma = GemmaInterpreterService()
    runner = SearchBenchmarkRunner(loader, engine, verifier, gemma)
    return runner

def test_ollama_status_offline_graceful():
    gemma = GemmaInterpreterService()
    status = gemma.check_ollama_status()
    assert "ollama_online" in status
    assert "target_model" in status
    # Should not throw any exception even if Ollama is not running

def test_gemma_fail_safe_interpretation():
    gemma = GemmaInterpreterService()
    # Test fallback extraction when model is offline
    res = gemma.interpret_query("Metformin 500mg Tablet")
    assert res.strength_mentioned == "500mg"
    assert res.dosage_form_mentioned == "Tablet"
    assert "offline" in res.reason.lower() or "ollama" in res.reason.lower() or res.is_available is True

def test_comparative_benchmark_execution(benchmark_suite):
    report = benchmark_suite.run_benchmark()
    assert report.total_test_cases == 8
    assert "mode_a_exact" in report.model_dump()
    assert "mode_b_fuzzy_deterministic" in report.model_dump()
    assert "mode_c_gemma_assisted" in report.model_dump()
    # Correct abstention rate on unknown medicines must be 100% for Mode B
    assert report.mode_b_fuzzy_deterministic["correct_abstention_rate"] == 100.0
    # Mode B must have higher top-1 accuracy than Mode A on messy/brand inputs
    assert report.mode_b_fuzzy_deterministic["top1_accuracy"] > report.mode_a_exact["top1_accuracy"]

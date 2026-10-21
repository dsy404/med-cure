import pytest
from app.services.data_loader import DataLoader
from app.services.medicine_search import MedicineSearchEngine
from app.schemas.medicine import RetrievalMethod

@pytest.fixture(scope="module")
def search_engine():
    loader = DataLoader()
    loader.load_all()
    engine = MedicineSearchEngine(loader)
    engine.ensure_indexed()
    return engine

def test_empty_query(search_engine):
    res = search_engine.search("")
    assert res.total_candidates == 0
    assert "empty" in res.message.lower()

def test_exact_match(search_engine):
    res = search_engine.search("Aceclofenac Tablets IP 100 mg")
    assert res.total_candidates >= 1
    top = res.candidates[0]
    assert top.retrieval_method == RetrievalMethod.EXACT_MATCH
    assert top.match_score == 100.0
    assert "GEN-2" == top.product.product_id

def test_verified_brand_alias(search_engine):
    res = search_engine.search("Dolo 650")
    assert res.total_candidates >= 1
    top = res.candidates[0]
    assert top.retrieval_method == RetrievalMethod.ALIAS_MATCH
    assert "paracetamol" in top.product.name.lower()
    assert "650" in top.product.name

def test_partial_match(search_engine):
    res = search_engine.search("Metformin 500")
    assert res.total_candidates >= 1
    assert any("metformin" in c.product.name.lower() for c in res.candidates)

def test_fuzzy_typo_search(search_engine):
    # Intentional typo: "paracetmol" instead of "paracetamol"
    res = search_engine.search("paracetmol")
    assert res.total_candidates >= 1
    assert any("paracetamol" in c.product.name.lower() for c in res.candidates)

def test_unknown_medicine_abstains(search_engine):
    # Query completely absent from catalogue
    res = search_engine.search("Xylopharmazine 9999mg Nonexistent")
    assert res.total_candidates == 0
    assert "no catalogue match found" in res.message.lower()

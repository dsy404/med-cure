import pytest
from pathlib import Path
from app.services.data_loader import DataLoader
from app.services.verification import VerificationEngine
from app.services.evidence_graph import EvidenceGraphService
from app.schemas.medicine import VerificationStatus

@pytest.fixture(scope="module")
def setup_services(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_evidence.db"
    loader = DataLoader()
    loader.load_all()
    verifier = VerificationEngine(loader.rs_benchmarks)
    graph_svc = EvidenceGraphService(db_path=db_file)
    return loader, verifier, graph_svc

def test_evidence_graph_record_and_retrieve(setup_services):
    loader, verifier, graph_svc = setup_services
    cand = loader.get_by_id("GEN-511") # Paracetamol 650
    assert cand is not None

    v_res = verifier.verify(
        query="Dolo 650",
        candidate=cand
    )

    # Build and record to SQLite
    graph_response = graph_svc.build_and_record(
        verification=v_res,
        candidate=cand,
        input_type="typed_search"
    )
    decision_id = graph_response.decision_id
    assert decision_id.startswith("DEC-")

    # Retrieve by decision ID from SQLite
    retrieved = graph_svc.get_by_decision_id(decision_id)
    assert retrieved is not None
    assert retrieved.decision_id == decision_id
    assert retrieved.input_evidence.query == "Dolo 650"
    assert retrieved.candidate.product_id == "GEN-511"
    assert retrieved.decision.verification_status == VerificationStatus.VERIFIED_FOR_PRICE_COMPARISON
    assert len(retrieved.attribute_checks) > 0

    # Test list_recent
    recent = graph_svc.list_recent(limit=10)
    assert len(recent) >= 1
    assert any(r["decision_id"] == decision_id for r in recent)

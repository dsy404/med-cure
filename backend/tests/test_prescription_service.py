import pytest
from pathlib import Path
from app.services.data_loader import DataLoader
from app.services.medicine_search import MedicineSearchEngine
from app.services.verification import VerificationEngine
from app.services.evidence_graph import EvidenceGraphService
from app.services.prescription_service import PrescriptionService
from app.services.pdf_report_service import PDFReportService
from app.schemas.prescription import PrescriptionItemCreate, PrescriptionItemUpdate

@pytest.fixture(scope="module")
def services(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_prescriptions.db"
    loader = DataLoader()
    loader.load_all()
    engine = MedicineSearchEngine(loader)
    engine.ensure_indexed()
    verifier = VerificationEngine(loader.rs_benchmarks)
    evidence_graph = EvidenceGraphService(db_path=db_file)
    rx_svc = PrescriptionService(
        db_path=db_file,
        data_loader=loader,
        search_engine=engine,
        verifier=verifier,
        evidence_graph=evidence_graph
    )
    return {
        "loader": loader,
        "engine": engine,
        "verifier": verifier,
        "evidence_graph": evidence_graph,
        "rx_svc": rx_svc
    }

def test_create_prescription(services):
    rx_svc = services["rx_svc"]
    rx = rx_svc.create_prescription(title="Cardiac and Diabetic Prescription")
    assert rx.prescription_id.startswith("RX-")
    assert rx.title == "Cardiac and Diabetic Prescription"
    assert rx.summary.total_items_count == 0
    assert rx.summary.confirmed_total_savings_inr == 0.0

def test_add_verified_item_and_unresolved_item_preserves_three_separate_totals(services):
    rx_svc = services["rx_svc"]
    rx = rx_svc.create_prescription(title="Multi-Tier Savings Test")

    # Item 1: Verified comparison with official Rajya Sabha benchmark (Atorvastatin 10mg)
    # PMBJP price = Rs 8, Avg Branded MRP = Rs 58, Saving = Rs 50
    item1 = rx_svc.add_item(
        prescription_id=rx.prescription_id,
        item_in=PrescriptionItemCreate(
            original_text="Tab Atorvastatin 10 mg 1-0-0",
            prescribed_name="Atorvastatin 10mg",
            prescribed_strength="10mg",
            prescribed_form="Tablet"
        )
    )
    assert item1.verification_status == "VERIFIED_FOR_PRICE_COMPARISON"
    assert item1.is_eligible_for_savings is True
    assert item1.calculated_saving_inr is not None
    assert item1.calculated_saving_inr > 0

    # Item 2: Unresolved item - Aceclofenac without strength, candidate has extra Paracetamol (GEN-1)
    # Combination conflict, must NOT be counted in confirmed savings
    item2 = rx_svc.add_item(
        prescription_id=rx.prescription_id,
        item_in=PrescriptionItemCreate(
            original_text="Tab Aceclofenac",
            prescribed_name="Aceclofenac",
            selected_candidate_id="GEN-1",
            user_reference_price_inr=50.0
        )
    )
    assert item2.verification_status != "VERIFIED_FOR_PRICE_COMPARISON"
    assert item2.is_eligible_for_savings is False

    # Fetch updated prescription
    updated_rx = rx_svc.get_prescription(rx.prescription_id)
    summary = updated_rx.summary

    # CRITICAL INVARIANT: 3 distinct totals
    # 1. Total items = 2
    assert summary.total_items_count == 2
    assert summary.verified_comparisons_count == 1
    assert summary.unresolved_items_count == 1

    # 2. Confirmed Potential Savings includes ONLY Item 1
    assert summary.confirmed_total_savings_inr == item1.calculated_saving_inr

    # 3. Item 2 is quarantined and its potential saving is isolated in excluded_potential_savings_inr
    assert summary.excluded_potential_savings_inr is not None
    # Excluded potential savings must NOT be added into confirmed savings!
    assert summary.confirmed_total_savings_inr != (item1.calculated_saving_inr + (summary.excluded_potential_savings_inr or 0.0))

def test_pdf_report_generation(services):
    rx_svc = services["rx_svc"]
    rx = rx_svc.create_prescription(title="PDF Test")
    rx_svc.add_item(
        prescription_id=rx.prescription_id,
        item_in=PrescriptionItemCreate(
            original_text="Dolo 650 mg",
            prescribed_name="Dolo 650",
            selected_candidate_id="GEN-511"
        )
    )
    updated_rx = rx_svc.get_prescription(rx.prescription_id)

    pdf_bytes = PDFReportService.generate_prescription_report(updated_rx)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic header
    assert pdf_bytes.startswith(b"%PDF")

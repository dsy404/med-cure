import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Response

from ..core.config import settings
from ..schemas.medicine import MedicineProduct, SearchResponse
from ..schemas.verification import VerificationResult, VerificationRequest
from ..schemas.evidence import EvidenceGraphResponse
from ..schemas.ai import GemmaInterpretation
from ..schemas.ocr import OCRPreviewResponse
from ..schemas.prescription import (
    PrescriptionItemCreate,
    PrescriptionItemUpdate,
    PrescriptionItem,
    PrescriptionResponse
)
from ..schemas.kendra import KendraSearchResponse

from ..services.data_loader import DataLoader
from ..services.medicine_search import MedicineSearchEngine
from ..services.verification import VerificationEngine
from ..services.gemma_interpreter import GemmaInterpreterService
from ..services.search_benchmark import SearchBenchmarkRunner, BenchmarkReport
from ..services.evidence_graph import EvidenceGraphService
from ..services.ocr_service import OCRService
from ..services.prescription_service import PrescriptionService
from ..services.pdf_report_service import PDFReportService
from ..services.kendra_service import KendraLocationService

router = APIRouter()

# Global singletons
_data_loader: Optional[DataLoader] = None
_search_engine: Optional[MedicineSearchEngine] = None
_verification_engine: Optional[VerificationEngine] = None
_gemma_service: Optional[GemmaInterpreterService] = None
_evidence_graph_service: Optional[EvidenceGraphService] = None
_ocr_service: Optional[OCRService] = None
_prescription_service: Optional[PrescriptionService] = None
_kendra_service: Optional[KendraLocationService] = None


def get_data_loader() -> DataLoader:
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
        _data_loader.load_all()
    return _data_loader


def get_search_engine(loader: DataLoader = Depends(get_data_loader)) -> MedicineSearchEngine:
    global _search_engine
    if _search_engine is None:
        _search_engine = MedicineSearchEngine(loader)
        _search_engine.ensure_indexed()
    return _search_engine


def get_verification_engine(loader: DataLoader = Depends(get_data_loader)) -> VerificationEngine:
    global _verification_engine
    if _verification_engine is None:
        _verification_engine = VerificationEngine(loader.rs_benchmarks)
    return _verification_engine


def get_gemma_service() -> GemmaInterpreterService:
    global _gemma_service
    if _gemma_service is None:
        _gemma_service = GemmaInterpreterService()
    return _gemma_service


def get_evidence_graph_service() -> EvidenceGraphService:
    global _evidence_graph_service
    if _evidence_graph_service is None:
        _evidence_graph_service = EvidenceGraphService()
    return _evidence_graph_service


def get_ocr_service(engine: MedicineSearchEngine = Depends(get_search_engine)) -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(search_engine=engine)
    return _ocr_service


def get_kendra_service() -> KendraLocationService:
    global _kendra_service
    if _kendra_service is None:
        _kendra_service = KendraLocationService()
    return _kendra_service


def get_prescription_service(
    loader: DataLoader = Depends(get_data_loader),
    engine: MedicineSearchEngine = Depends(get_search_engine),
    verifier: VerificationEngine = Depends(get_verification_engine),
    evidence_graph: EvidenceGraphService = Depends(get_evidence_graph_service)
) -> PrescriptionService:
    global _prescription_service
    if _prescription_service is None:
        _prescription_service = PrescriptionService(
            data_loader=loader,
            search_engine=engine,
            verifier=verifier,
            evidence_graph=evidence_graph
        )
    return _prescription_service


# ---------------------------------------------------------
# Health and Diagnostics Endpoints
# ---------------------------------------------------------

@router.get("/health")
def get_health(
    loader: DataLoader = Depends(get_data_loader),
    kendra_svc: KendraLocationService = Depends(get_kendra_service),
    gemma: GemmaInterpreterService = Depends(get_gemma_service)
):
    """
    Returns verified backend health status, dataset loading counts, Kendra network count, and provenance.
    """
    llm_info = gemma.check_ollama_status()
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "datasets": {
            "loaded": loader.loaded,
            "errors": loader.load_errors,
            "generic_products_total": loader.stats["generic_count"],
            "generic_usable_prices": loader.stats["generic_usable_price_count"],
            "ceiling_price_references": loader.stats["ceiling_count"],
            "rs_official_benchmarks": loader.stats["rs_benchmark_count"],
            "generic_file_exists": loader.generic_csv_path.exists(),
            "ceiling_file_exists": loader.ceiling_csv_path.exists(),
            "quality_report_exists": (loader.data_dir / "data_quality_report.txt").exists(),
            "verified_kendras_total": len(kendra_svc.kendras)
        },
        "llm_status": llm_info
    }


@router.get("/health/llm")
def get_llm_health(gemma: GemmaInterpreterService = Depends(get_gemma_service)):
    """
    Returns local Ollama daemon connectivity and model availability status.
    """
    return gemma.check_ollama_status()


# ---------------------------------------------------------
# Medicine Search & Verification Endpoints
# ---------------------------------------------------------

@router.get("/medicines/search", response_model=SearchResponse)
def search_medicines(
    q: str = Query(..., description="Medicine brand name, generic molecule, or dosage"),
    limit: int = Query(10, ge=1, le=50, description="Max candidates to return"),
    include_ceiling: bool = Query(True, description="Whether to include DPCO ceiling price references"),
    engine: MedicineSearchEngine = Depends(get_search_engine)
):
    """
    Multi-stage candidate retrieval with exact match, verified brand alias,
    normalized match, token containment, and RapidFuzz typo tolerance.
    """
    return engine.search(query=q, limit=limit, include_ceiling_prices=include_ceiling)


@router.get("/medicines/{product_id}", response_model=MedicineProduct)
def get_medicine_by_id(
    product_id: str,
    loader: DataLoader = Depends(get_data_loader)
):
    """
    Returns verified catalogue record by unique stable product ID (e.g. 'GEN-10', 'CEIL-15').
    """
    product = loader.get_by_id(product_id.strip())
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Medicine product with ID '{product_id}' was not found in the verified catalogue."
        )
    return product


@router.post("/verify", response_model=VerificationResult)
def verify_candidate_match(
    req: VerificationRequest,
    loader: DataLoader = Depends(get_data_loader),
    verifier: VerificationEngine = Depends(get_verification_engine),
    evidence_graph: EvidenceGraphService = Depends(get_evidence_graph_service)
):
    """
    Deterministically evaluates clinical attribute compatibility (molecules, strengths, forms)
    and verifies price evidence suitability before permitting savings calculations.
    Automatically persists the decision to the Medicine Evidence Graph.
    """
    candidate = loader.get_by_id(req.candidate_product_id.strip())
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate medicine '{req.candidate_product_id}' not found in catalogue."
        )

    v_res = verifier.verify(
        query=req.query,
        candidate=candidate,
        user_ref_price=req.user_reported_reference_price_inr,
        user_ref_unit=req.user_reported_unit_size,
        reference_brand=req.reference_brand_name
    )

    # Persist decision to SQLite Evidence Graph
    evidence_graph.build_and_record(
        verification=v_res,
        candidate=candidate,
        user_ref_price=req.user_reported_reference_price_inr,
        user_ref_unit=req.user_reported_unit_size,
        reference_brand=req.reference_brand_name,
        input_type="typed_search"
    )

    return v_res


# ---------------------------------------------------------
# Medicine Evidence Graph Endpoints
# ---------------------------------------------------------

@router.get("/evidence/{decision_id}", response_model=EvidenceGraphResponse)
def get_evidence_record(
    decision_id: str,
    evidence_graph: EvidenceGraphService = Depends(get_evidence_graph_service)
):
    """
    Returns the complete traceable Medicine Evidence Graph chain:
    Input -> Extraction -> Candidate -> Verification Checks -> Price Evidence -> Decision
    """
    record = evidence_graph.get_by_decision_id(decision_id.strip())
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Evidence decision record '{decision_id}' was not found in the evidence store."
        )
    return record


@router.get("/evidence", response_model=List[Dict[str, Any]])
def list_recent_evidence_records(
    limit: int = Query(20, ge=1, le=100),
    evidence_graph: EvidenceGraphService = Depends(get_evidence_graph_service)
):
    """
    Returns recent verification decisions stored in the SQLite evidence repository.
    """
    return evidence_graph.list_recent(limit=limit)


# ---------------------------------------------------------
# Visual Medicine Recognition & OCR Endpoints
# ---------------------------------------------------------

@router.post("/recognition/preview", response_model=OCRPreviewResponse)
async def preview_medicine_image(
    file: UploadFile = File(..., description="Medicine packaging or blister pack photograph"),
    ocr_svc: OCRService = Depends(get_ocr_service)
):
    """
    Accepts an uploaded photograph of a medicine packaging or blister pack.
    Assesses image quality (blur, resolution, lighting), performs EasyOCR extraction,
    and returns detected text, confidence values, and matched candidate medicines.
    """
    # Validate mime type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type and file.content_type.lower() not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file.content_type}'. Please upload JPEG, PNG, or WEBP images."
        )

    # Read image content
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum permitted limit (10 MB)."
        )

    return ocr_svc.process_image_bytes(contents, mime_type=file.content_type or "image/jpeg")


# ---------------------------------------------------------
# Whole-Prescription Savings Engine Endpoints
# ---------------------------------------------------------

@router.post("/prescriptions", response_model=PrescriptionResponse)
def create_prescription(
    title: str = Query("Prescription Savings Assessment", description="Prescription title"),
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Creates a new multi-item prescription container in the SQLite repository.
    """
    return rx_svc.create_prescription(title=title)


@router.get("/prescriptions/{rx_id}", response_model=PrescriptionResponse)
def get_prescription_by_id(
    rx_id: str,
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Retrieves a prescription with itemized line items and three separate totals.
    """
    rx = rx_svc.get_prescription(rx_id.strip())
    if not rx:
        raise HTTPException(
            status_code=404,
            detail=f"Prescription '{rx_id}' not found."
        )
    return rx


@router.post("/prescriptions/{rx_id}/items", response_model=PrescriptionItem)
def add_prescription_item(
    rx_id: str,
    item_in: PrescriptionItemCreate,
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Adds a prescribed medicine line item, matches candidate generics,
    and calculates clinical verification and price comparison.
    """
    return rx_svc.add_item(rx_id.strip(), item_in)


@router.patch("/prescriptions/{rx_id}/items/{item_id}", response_model=PrescriptionItem)
def update_prescription_item(
    rx_id: str,
    item_id: str,
    update_in: PrescriptionItemUpdate,
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Updates or clarifies a prescription item (e.g. user provides missing strength,
    selects specific candidate, or enters pharmacy price quote).
    """
    updated = rx_svc.update_item(rx_id.strip(), item_id.strip(), update_in)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Prescription item '{item_id}' not found in prescription '{rx_id}'."
        )
    return updated


@router.delete("/prescriptions/{rx_id}/items/{item_id}")
def delete_prescription_item(
    rx_id: str,
    item_id: str,
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Removes a line item from the prescription.
    """
    success = rx_svc.remove_item(rx_id.strip(), item_id.strip())
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Prescription item '{item_id}' not found."
        )
    return {"status": "deleted", "item_id": item_id}


@router.post("/prescriptions/{rx_id}/analyze", response_model=PrescriptionResponse)
def analyze_prescription(
    rx_id: str,
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Re-evaluates all items in the prescription, re-runs deterministic verification,
    and updates the 3-tier totals (Confirmed Savings, Unresolved Items, Excluded Estimate).
    """
    rx = rx_svc.get_prescription(rx_id.strip())
    if not rx:
        raise HTTPException(status_code=404, detail=f"Prescription '{rx_id}' not found.")
    return rx


@router.get("/prescriptions/{rx_id}/pdf")
def download_prescription_pdf(
    rx_id: str,
    rx_svc: PrescriptionService = Depends(get_prescription_service)
):
    """
    Generates a deterministic, printable ReportLab PDF report containing itemized
    evidence IDs, price provenance, 3-tier totals, and pharmacist consultation notices.
    """
    rx = rx_svc.get_prescription(rx_id.strip())
    if not rx:
        raise HTTPException(status_code=404, detail=f"Prescription '{rx_id}' not found.")

    pdf_bytes = PDFReportService.generate_prescription_report(rx)
    filename = f"MedLedger_Prescription_{rx_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# ---------------------------------------------------------
# Jan Aushadhi Kendra Location Finder Endpoints
# ---------------------------------------------------------

@router.get("/locations/kendras", response_model=KendraSearchResponse)
def find_kendras(
    q: Optional[str] = Query(None, description="City, district, state, or 6-digit PIN code"),
    lat: Optional[float] = Query(None, description="User latitude for distance calculation"),
    lng: Optional[float] = Query(None, description="User longitude for distance calculation"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    kendra_svc: KendraLocationService = Depends(get_kendra_service)
):
    """
    Searches attributable Jan Aushadhi Kendras across India by city/pincode or geolocation.
    Includes great-circle distance calculation and explicit stock availability boundary warning.
    """
    return kendra_svc.search_kendras(
        query=q,
        user_lat=lat,
        user_lng=lng,
        max_results=limit
    )


# ---------------------------------------------------------
# Benchmark and Data Audit Endpoints
# ---------------------------------------------------------

@router.get("/benchmarks")
def get_official_benchmarks(loader: DataLoader = Depends(get_data_loader)):
    """
    Returns official government parliamentary benchmarks (Rajya Sabha Session 255)
    surveying average branded MRP vs PMBJP generic prices.
    """
    return {
        "source": "Rajya Sabha Session 255 Annexure 1784-B",
        "authority": "Ministry of Chemicals and Fertilizers, Department of Pharmaceuticals",
        "total_records": len(loader.rs_benchmarks),
        "benchmarks": loader.rs_benchmarks
    }


@router.get("/data-quality-report")
def get_data_quality_report(loader: DataLoader = Depends(get_data_loader)):
    """
    Returns the Phase 2 data quality audit report and provenance documentation.
    """
    report_path = loader.data_dir / "data_quality_report.txt"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Data quality report not found on disk.")
    
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return {
        "file": str(report_path),
        "content": content,
        "stats": loader.stats
    }


@router.get("/ai/status")
def get_ai_status(gemma: GemmaInterpreterService = Depends(get_gemma_service)):
    """
    Returns Ollama local runtime connectivity and Gemma model status.
    """
    return gemma.check_ollama_status()


@router.post("/ai/interpret", response_model=GemmaInterpretation)
def interpret_query_with_ai(
    q: str = Query(..., description="Messy medicine query"),
    gemma: GemmaInterpreterService = Depends(get_gemma_service)
):
    """
    Interprets messy or ambiguous input using local Gemma model.
    Fails safely to deterministic parsing when Ollama is offline.
    """
    return gemma.interpret_query(q)


@router.get("/benchmark", response_model=BenchmarkReport)
def run_search_benchmark(
    loader: DataLoader = Depends(get_data_loader),
    engine: MedicineSearchEngine = Depends(get_search_engine),
    verifier: VerificationEngine = Depends(get_verification_engine),
    gemma: GemmaInterpreterService = Depends(get_gemma_service)
):
    """
    Evaluates Mode A (Exact), Mode B (Fuzzy+Deterministic), and Mode C (Gemma-assisted)
    on a fixed benchmark of clinical and adversarial test cases.
    """
    runner = SearchBenchmarkRunner(loader, engine, verifier, gemma)
    return runner.run_benchmark()

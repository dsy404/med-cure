import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["datasets"]["loaded"] is True
    assert data["datasets"]["generic_products_total"] == 2439
    assert data["datasets"]["ceiling_price_references"] == 915

def test_api_search_success(client):
    response = client.get("/api/medicines/search?q=Paracetamol&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Paracetamol"
    assert data["total_candidates"] > 0
    assert len(data["candidates"]) <= 5
    assert "paracetamol" in data["candidates"][0]["product"]["name"].lower()

def test_api_search_empty(client):
    response = client.get("/api/medicines/search?q=")
    assert response.status_code == 200
    data = response.json()
    assert data["total_candidates"] == 0
    assert "empty" in data["message"].lower()

def test_api_get_product_by_id(client):
    # Test valid product
    response = client.get("/api/medicines/GEN-1")
    assert response.status_code == 200
    prod = response.json()
    assert prod["product_id"] == "GEN-1"
    assert "Aceclofenac" in prod["name"]

    # Test invalid product
    err_res = client.get("/api/medicines/GEN-INVALID-999")
    assert err_res.status_code == 404
    assert "not found" in err_res.json()["detail"].lower()

def test_api_data_quality_report(client):
    response = client.get("/api/data-quality-report")
    assert response.status_code == 200
    data = response.json()
    assert "MoleculeLedger AI" in data["content"] or "Data Quality Report" in data["content"]
    assert data["stats"]["generic_count"] == 2439

def test_api_kendra_search(client):
    response = client.get("/api/locations/kendras?q=110029")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 1
    assert "Stock availability has not been verified" in data["stock_verification_disclaimer"]

def test_api_llm_health(client):
    response = client.get("/api/health/llm")
    assert response.status_code == 200
    data = response.json()
    assert "ollama_online" in data
    assert "target_model" in data

def test_api_prescription_lifecycle_and_pdf(client):
    # 1. Create prescription
    res_create = client.post("/api/prescriptions?title=Full+Test+Prescription")
    assert res_create.status_code == 200
    rx = res_create.json()
    rx_id = rx["prescription_id"]
    assert rx_id.startswith("RX-")

    # 2. Add verified line item
    res_add = client.post(
        f"/api/prescriptions/{rx_id}/items",
        json={
            "original_text": "Tab Atorvastatin 10mg",
            "prescribed_name": "Atorvastatin 10mg",
            "prescribed_strength": "10mg",
            "prescribed_form": "Tablet"
        }
    )
    assert res_add.status_code == 200
    item = res_add.json()
    assert item["verification_status"] == "VERIFIED_FOR_PRICE_COMPARISON"
    dec_id = item["evidence_decision_id"]
    assert dec_id is not None

    # 3. Test evidence graph endpoint
    ev_res = client.get(f"/api/evidence/{dec_id}")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["decision_id"] == dec_id
    assert ev_data["candidate"]["product_id"].startswith("GEN-")

    # 4. Test PDF download endpoint
    pdf_res = client.get(f"/api/prescriptions/{rx_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000
    assert pdf_res.content.startswith(b"%PDF")


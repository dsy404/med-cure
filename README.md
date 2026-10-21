# MedLedger
## Evidence-First Medicine Savings Intelligence Platform

> **Tagline:** *Every medicine match. Every price. Every claim backed by evidence.*

MedLedger is an evidence-first medicine price transparency, clinical verification, and prescription savings intelligence platform tailored to the Indian healthcare ecosystem.

Unlike generic conversational chatbots or static dashboards, MedLedger operates on **documented product records, staged multi-tier retrieval, attribute-by-attribute clinical verification, and verifiable price evidence**. It is architected with strict uncertainty handling—meaning the system **abstains from making unsupported claims, refuses to guess unverified medicine identities, and strictly isolates unverified prescription items from confirmed savings totals**.

---

## 1. Architectural Overview

```text
React + TypeScript Frontend (Vite + Accessible Design System)
        |
        v  HTTP / REST JSON & Multipart
FastAPI Backend Application
        |
        +-- Medicine Search Service (Exact, Brand Aliases, RapidFuzz Typo-Sort)
        +-- OCR & Image Processing Service (OpenCV Quality Audit + EasyOCR Engine)
        +-- Clinical Verification Engine (Active Salt Overlap, Strength, Formulation, Release)
        +-- Price Comparison Engine (Pack Normalization, Statutory DPCO vs PMBJP MRP)
        +-- Medicine Evidence Graph Service (SQLite Persistent Linked Records)
        +-- Whole-Prescription Savings Engine (3-Tier Totals: Confirmed, Quarantined, Excluded)
        +-- PDF Report Service (Deterministic ReportLab Pharmacist Export)
        +-- Jan Aushadhi Kendra Location Service (Haversine Proximity + Stock Boundary)
        +-- Local AI / Gemma Adapter (Structured Interpretation, Safe Offline Fallback)
        |
        v
Cleaned PMBJP & DPCO Catalogue Datasets + SQLite Evidence Store
```

---

## 2. Core Pillars & Non-Negotiable Rules

### A. Real Functionality over Fabrication
- Search queries the genuine cleaned datasets: 2,439 Jan Aushadhi generic records and 915 NPPA DPCO statutory ceiling price caps.
- Never hardcodes search results or fabricates medicines, manufacturers, prices, or savings.
- 344 records in the PMBJP catalogue with zero or unlisted MRP are explicitly flagged and quarantined from savings calculations.

### B. Evidence Over Confidence
The system categorizes candidate comparisons into explicit, verifiable states:
- `VERIFIED_FOR_PRICE_COMPARISON`: Active ingredients, strengths, and dosage forms match, and valid price evidence exists.
- `NEEDS_CLARIFICATION`: Query omitted strength, or candidate formulation/release profile differs.
- `INCOMPARABLE_PRICE_BASIS`: Rejects comparing a statutory government ceiling cap (DPCO 2013) against a retail pharmacy quote.
- `INSUFFICIENT_EVIDENCE`: Product has zero listed MRP or reference retail quote is absent.
- `NO_CATALOGUE_MATCH`: Honestly abstains rather than returning arbitrary false matches.

### C. The Signature Feature: The Medicine Evidence Graph
Every comparison creates an immutable, traceable record linking:
1. **Input Node**: User query, input type, reference brand quote, captured timestamp.
2. **Extraction Node**: Normalized query, detected molecules, strengths, dosage form, brand alias applied.
3. **Candidate Node**: Stable catalogue ID, official name, pack size, MRP, source dataset provenance.
4. **Attribute Checks**: Itemized active ingredient overlap, strength match, formulation match, release profile.
5. **Price Evidence Node**: Source organization, price type, pack unit normalization formula applied.
6. **Decision Node**: Final verification status, savings eligibility, plain-language summary, clinical disclaimers.

### D. Whole-Prescription Savings Engine: 3 Distinct Totals
- **Total A (Confirmed Potential Savings):** Sum of savings ONLY for items that pass deterministic verification and have valid source-backed prices.
- **Total B (Unresolved Items):** Count of items with missing strengths, combination conflicts, or unlisted prices, strictly quarantined from totals.
- **Total C (Excluded Potential Savings):** Informational estimate for unresolved items, strictly excluded from the confirmed total savings.

### E. Jan Aushadhi Kendra Locator & Stock Boundary
- Attributable PMBJP directory network across Indian states and metropolitan cities.
- Distance computed via the spherical Haversine formula.
- **Non-Negotiable Stock Disclaimer:** *"Stock availability has not been verified. Contact the Kendra before visiting."*

---

## 3. Verified Official Datasets

Located in the `data/` directory:
1. `generic_products_clean.csv`: 2,439 rows from the Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP) catalogue.
   - 2,095 rows have verified positive MRP.
   - 344 rows have zero MRP (marked `usable_for_price_comparison = False`).
2. `ceiling_prices_clean.csv`: 915 statutory ceiling price records fixed by the National Pharmaceutical Pricing Authority (NPPA / DPCO 2013).
   - Marked `reference_only` because ceiling prices are legal caps excluding taxes, not retail selling quotes.
3. `RS_Session_255_AU_1784_B.csv`: Official government surveyed comparison records submitted to the Rajya Sabha (Ministry of Chemicals & Fertilizers) detailing average branded market-leader MRPs vs PMBJP generic prices.
4. `data_quality_report.txt`: Phase 2 data cleaning audit report detailing column distributions, null counts, and cleaning decisions.

---

## 4. Local AI Integration (Gemma & Ollama)

### Role & Guardrails
- **Runtime**: Local [Ollama](https://ollama.com) daemon running on `http://localhost:11434`.
- **Target Model**: `gemma2:2b` (Google Gemma 2, 2 Billion parameters open-weight model).
- **Responsibilities**:
  - Interprets messy, unstructured, or misspelled user search queries.
  - Extracts explicitly mentioned clinical strengths and forms.
  - Highlights missing attributes for clarification.
  - Produces schema-constrained JSON only.
- **Fail-Safe Mechanism**:
  - If Ollama is offline or the model is not pulled, the backend automatically falls back to deterministic extraction and staged search without breaking or pretending AI executed.
  - Deterministic search, verification, price arithmetic, evidence storage, and PDF generation work completely without Ollama.

---

## 5. Prerequisites & Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.14.3 64-bit)
- Node.js v18+ (Tested on Node.js v24.14.0)
- npm 9+ (Tested on npm 11.9.0)
- (Optional for AI mode) [Ollama](https://ollama.com) with `ollama pull gemma2:2b`

### Installation Steps

1. **Clone or enter the project directory:**
   ```powershell
   cd c:\Users\HP\Desktop\mlh
   ```

2. **Install Python backend dependencies:**
   ```powershell
   python -m pip install -r backend/requirements.txt
   ```

3. **Install Frontend dependencies:**
   ```powershell
   cd frontend
   npm install
   cd ..
   ```

---

## 6. How to Run Locally

### Option 1: Quick PowerShell Scripts
Open two PowerShell terminals in `c:\Users\HP\Desktop\mlh`:

**Terminal 1 — Backend:**
```powershell
.\run_backend.ps1
```
*(Starts FastAPI on `http://127.0.0.1:8000`)*

**Terminal 2 — Frontend:**
```powershell
.\run_frontend.ps1
```
*(Starts Vite dev server on `http://localhost:5173`)*

---

### Option 2: Manual Commands

**Backend:**
```powershell
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```powershell
cd frontend
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 7. Running the Automated Test Suite

Run all tests:
```powershell
python -m pytest -v
```
*(Or run `.\run_tests.ps1`)*

**Current Test Results:**
- **`46 passed in 14.60s`** (100% pass rate)
  - `test_search.py`: Exact matching, typo-tolerant RapidFuzz, alias matching, abstention.
  - `test_verification.py`: Salt overlap, single vs combination regression, strength checks, pack normalization.
  - `test_prescription_service.py`: Multi-item lifecycle, 3-tier totals, ReportLab PDF generation.
  - `test_ocr_service.py`: OpenCV blur/sharpness, brightness evaluation, text normalization.
  - `test_kendra_service.py`: Attributable PMBJP directory, Haversine formula, stock boundary disclaimer.
  - `test_evidence_graph.py`: SQLite persistence, decision retrieval, recent decisions audit.
  - `test_api.py`: Full FastAPI endpoint coverage.
  - `test_ai_benchmark.py`: 3-mode comparative evaluation.

---

## 8. Complete API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check, dataset loading counts, Kendra network count, provenance |
| `/api/health/llm` | `GET` | Check local Ollama daemon connectivity and model status |
| `/api/medicines/search` | `GET` | Staged candidate retrieval (`q`, `limit`, `include_ceiling`) |
| `/api/medicines/{product_id}` | `GET` | Look up catalogue product by stable ID (`GEN-xx`, `CEIL-xx`) |
| `/api/verify` | `POST` | Deterministically verify candidate, calculate savings, and record evidence |
| `/api/evidence/{decision_id}` | `GET` | Retrieve complete Medicine Evidence Graph chain for decision |
| `/api/evidence` | `GET` | List recent verification decisions stored in SQLite |
| `/api/recognition/preview` | `POST` | Upload packaging image for OpenCV quality audit and EasyOCR extraction |
| `/api/prescriptions` | `POST` | Create a new multi-item prescription container |
| `/api/prescriptions/{id}` | `GET` | Get prescription with line items and 3 separate summary totals |
| `/api/prescriptions/{id}/items` | `POST` | Add prescribed line item, match generic, and run clinical verification |
| `/api/prescriptions/{id}/items/{item_id}` | `PATCH` | Clarify missing attributes or update reference price |
| `/api/prescriptions/{id}/items/{item_id}` | `DELETE` | Remove line item from prescription |
| `/api/prescriptions/{id}/analyze` | `POST` | Re-analyze prescription items and recalculate 3-tier totals |
| `/api/prescriptions/{id}/pdf` | `GET` | Deterministic ReportLab PDF report generation with evidence IDs |
| `/api/locations/kendras` | `GET` | Search PMBJP Kendras by pincode/city or GPS coordinates (Haversine) |
| `/api/benchmarks` | `GET` | Retrieve official Rajya Sabha parliamentary survey price pairs |
| `/api/benchmark` | `GET` | Run 3-mode comparative evaluation across test cases |
| `/api/data-quality-report` | `GET` | Return Phase 2 data quality audit report |
| `/api/ai/status` | `GET` | Check local Ollama daemon and Gemma model status |
| `/api/ai/interpret` | `POST` | Structured query interpretation via local Gemma model |

Interactive Swagger documentation is available at **`http://127.0.0.1:8000/docs`**.

---

## 9. Clinical & Legal Disclaimer

MedLedger is an informational price transparency tool designed to promote pharmaceutical affordability in India. **It does not provide medical advice, diagnosis, treatment, or clinical substitution approval.** 

Generic substitution must always be evaluated and approved by a qualified registered medical practitioner or licensed pharmacist.

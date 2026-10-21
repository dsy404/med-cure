# MedWise 🩺

### Evidence-First Medicine Savings Intelligence & Clinical Verification Platform

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026-ff7a00?style=for-the-badge&logo=hacktoberfest&logoColor=white)](https://hacktoberfest.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/Tests-46%20Passed%20(100%25)-success?style=for-the-badge&logo=pytest&logoColor=white)](backend/tests/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)

> **"Every medicine match. Every price. Every claim backed by evidence."**

---

## 🌟 Why MedWise?

In India, **out-of-pocket pharmaceutical expenditure accounts for over 50% of direct healthcare costs**, driving millions of families into financial distress each year. While affordable generic medicines exist through government initiatives like the **Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP)**, patients and doctors face major hurdles:

1. **Information Asymmetry**: Branded drugs are aggressively marketed while equivalent generic options remain unknown.
2. **Clinical Substitution Risk**: Substituting medicines based on loose name matching without verifying salt composition, active strength, and release profile can be dangerous.
3. **The "Hallucinating AI" Trap**: Large language models often hallucinate nonexistent drug combinations, invent prices, or give medical advice without verifiable provenance.

**MedWise solves this through deterministic, evidence-backed software.** It operates strictly on verified government datasets, enforces rigorous clinical verification rules, and maintains an immutable **Medicine Evidence Graph** for every recommendation.

---

## 📚 Table of Contents

- [Core Features](#-core-features)
- [System Architecture](#-system-architecture)
- [Verified Datasets Provenance](#-verified-datasets-provenance)
- [Quickstart: Local Installation Guide](#-quickstart-local-installation-guide)
  - [Prerequisites](#prerequisites)
  - [Step 1: Clone Repository](#step-1-clone-repository)
  - [Step 2: Backend Setup](#step-2-backend-setup)
  - [Step 3: Frontend Setup](#step-3-frontend-setup)
- [Running Automated Tests](#-running-automated-tests)
- [Local AI / Gemma Setup (Optional)](#-local-ai--gemma-setup-optional)
- [REST API Reference](#-rest-api-reference)
- [Hacktoberfest & Contributing](#-hacktoberfest--contributing)
- [Clinical & Legal Disclaimer](#-clinical--legal-disclaimer)
- [License](#-license)

---

## ✨ Core Features

| Feature | Description |
| :--- | :--- |
| **🔍 Staged Search Engine** | Combines exact token matching, brand-to-generic alias expansion (e.g. *Crocin → Paracetamol*), and typo-tolerant RapidFuzz matching across 2,439 genuine PMBJP catalogue entries. |
| **⚖️ Deterministic Clinical Verification** | Itemizes molecule overlap, strength equivalence, dosage formulation (tablet vs syrup), and release profile (IR vs SR). Rejects comparisons when attributes mismatch. |
| **🧾 3-Tier Whole-Prescription Studio** | Multi-item basket manager with **3 distinct totals**: Confirmed Savings, Quarantined Items (unresolved strengths/formulations), and Excluded Savings. |
| **📄 Pharmacist PDF Report** | Generates deterministic, printable PDF prescription handover reports via ReportLab with embedded QR codes, clinical disclaimers, and audit IDs. |
| **📷 Packaging OCR & Quality Audit** | OpenCV pipeline assessing brightness, blur (Laplacian variance), and foil glare before running EasyOCR extraction on medicine blister packs. |
| **📍 Jan Aushadhi Kendra Locator** | Pincode and GPS-assisted Kendra finder using spherical Haversine formulas with a mandatory stock boundary disclaimer. |
| **🕸️ Medicine Evidence Graph** | SQLite-backed immutable chain linking user query → extraction node → catalogue candidate → attribute verification → price evidence → final decision. |

---

## 🏗️ System Architecture

```text
               +--------------------------------------------+
               |     React 18 + TypeScript Web Client       |
               | (Vite, Accessible Design System, Tailwind) |
               +---------------------+----------------------+
                                     |
                                     | HTTP REST & Multipart
                                     v
               +--------------------------------------------+
               |         FastAPI Backend Application        |
               +---------------------+----------------------+
                                     |
        +----------------------------+----------------------------+
        |                            |                            |
        v                            v                            v
+------------------+       +------------------+         +------------------+
| Medicine Search  |       | Clinical Verifier|         | Prescription Hub |
| Exact, Aliases,  |       | Salt Overlap,    |         | 3-Tier Totals,   |
| RapidFuzz Typo   |       | Strength & Form  |         | ReportLab PDF    |
+------------------+       +------------------+         +------------------+
        |                            |                            |
        +----------------------------+----------------------------+
                                     |
                                     v
               +--------------------------------------------+
               |          Medicine Evidence Graph           |
               | (SQLite Persistent Audit Trail & Decisions)|
               +---------------------+----------------------+
                                     |
                                     v
               +--------------------------------------------+
               |         Cleaned Government Datasets        |
               |   - PMBJP Generic Catalogue (2,439 items)  |
               |   - NPPA DPCO Ceiling Price Caps (915 items)|
               |   - Rajya Sabha Survey Records (Session 255)|
               +--------------------------------------------+
```

---

## 📊 Verified Datasets Provenance

All datasets reside in the [`data/`](data/) directory and represent verified Indian public health sources:

1. **`generic_products_clean.csv`**: 2,439 generic formulations from the official Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP) catalogue.
   - 2,095 entries with verified MRP.
   - 344 entries with unlisted MRP quarantined from savings calculations.
2. **`ceiling_prices_clean.csv`**: 915 statutory ceiling price caps fixed under the Drugs (Prices Control) Order, 2013 (DPCO 2013) by the National Pharmaceutical Pricing Authority (NPPA).
3. **`RS_Session_255_AU_1784_B.csv`**: Official price comparison data presented to the Rajya Sabha (Ministry of Chemicals & Fertilizers) comparing branded market-leader MRPs against PMBJP retail prices.
4. **`data_quality_report.txt`**: Complete Phase 2 dataset cleaning audit documenting column distributions, null counts, and quarantine rules.

---

## 🚀 Quickstart: Local Installation Guide

Anyone can clone and run MedWise locally in under 5 minutes.

### Prerequisites

- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.14)
- **Node.js 18+** & **npm 9+**
- **Git**

### Step 1: Clone Repository

```bash
git clone https://github.com/dsy404/med-cure.git
cd med-cure
```

### Step 2: Backend Setup

Open a terminal in the project root:

```bash
# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Start the FastAPI backend server
# Windows:
.\run_backend.ps1
# macOS / Linux / Manual:
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend will be live at **`http://127.0.0.1:8000`**.  
Interactive Swagger API documentation is available at **`http://127.0.0.1:8000/docs`**.

### Step 3: Frontend Setup

Open a second terminal window in the project root:

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite dev server
npm run dev
# (Or on Windows: .\run_frontend.ps1 from root)
```

Open your browser and visit **`http://localhost:5173`**! 🎉

---

## 🧪 Running Automated Tests

MedWise features a 100% passing test suite with 46 automated tests across 8 test suites:

```bash
# From project root with virtual environment activated:
python -m pytest -v
```
*(On Windows you can also run `.\run_tests.ps1`)*

### Test Coverage Highlights:
- **`test_search.py`**: Exact token matches, RapidFuzz typo tolerance, alias resolution, abstention on unknown drugs.
- **`test_verification.py`**: Active salt overlap, single vs multi-ingredient combination safety, dosage form compatibility.
- **`test_prescription_service.py`**: Multi-item prescription lifecycle, 3-tier calculations, ReportLab PDF generation.
- **`test_ocr_service.py`**: OpenCV image sharpness, brightness metrics, foil glare handling.
- **`test_kendra_service.py`**: Haversine distance calculations, nearest PMBJP Kendras, stock boundary disclaimer enforcement.
- **`test_evidence_graph.py`**: SQLite persistence, decision retrieval, and tamper-resistant audit trails.
- **`test_api.py`**: End-to-end integration tests for all FastAPI REST routes.
- **`test_ai_benchmark.py`**: 3-mode comparative benchmark evaluation.

---

## 🤖 Local AI / Gemma Setup (Optional)

MedWise is designed to work **100% offline and deterministically** without AI. However, for natural language interpretation of messy search queries, you can optionally connect a local Gemma model:

1. Download and install [Ollama](https://ollama.com/).
2. Pull the lightweight open-weight model:
   ```bash
   ollama pull gemma2:2b
   ```
3. Start the Ollama daemon (`ollama serve`). MedWise will automatically detect it on `http://localhost:11434` and use it for query normalization, safely falling back to deterministic extraction if Ollama is unavailable.

---

## 🔌 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check, catalogue product count, Kendra store count |
| `/api/medicines/search` | `GET` | Staged candidate medicine search (`q`, `limit`, `include_ceiling`) |
| `/api/medicines/{product_id}` | `GET` | Retrieve catalogue product by stable ID (`GEN-xx`, `CEIL-xx`) |
| `/api/verify` | `POST` | Deterministically verify candidate equivalence and calculate price savings |
| `/api/evidence/{decision_id}` | `GET` | Retrieve full Medicine Evidence Graph chain for any decision |
| `/api/evidence` | `GET` | Audit list of recent verification decisions from SQLite |
| `/api/prescriptions` | `POST` | Create a new multi-item prescription container |
| `/api/prescriptions/{id}` | `GET` | Retrieve prescription items and calculated 3-tier totals |
| `/api/prescriptions/{id}/items` | `POST` | Add prescribed medicine, match generic candidate, run verification |
| `/api/prescriptions/{id}/pdf` | `GET` | Download deterministic printable PDF summary report |
| `/api/locations/kendras` | `GET` | Find nearest PMBJP Jan Aushadhi Kendras by pincode or GPS coordinates |
| `/api/recognition/preview` | `POST` | Upload packaging image for OpenCV quality audit and OCR extraction |
| `/api/benchmarks` | `GET` | Retrieve official Rajya Sabha parliamentary survey price pairs |
| `/api/ai/status` | `GET` | Check local Ollama daemon and Gemma model status |

Full interactive API specs are available at `http://127.0.0.1:8000/docs`.

---

## 🎃 Hacktoberfest & Contributing

We actively participate in **Hacktoberfest** and welcome contributions from the global open-source community! 

### How to Get Involved:
- Check our [**`CONTRIBUTING.md`**](CONTRIBUTING.md) for full development standards, branching rules, and PR checklist.
- Browse [Good First Issues](https://github.com/dsy404/med-cure/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) for beginner-friendly tasks.
- Help us expand Indian brand aliases in [`brand_aliases.py`](backend/app/services/brand_aliases.py).
- Help us expand PMBJP Kendra coverage in [`kendra_service.py`](backend/app/services/kendra_service.py).
- Help us add regional Indian language support in the frontend!

---

## ⚠️ Clinical & Legal Disclaimer

> **MedWise is an informational price transparency tool designed to promote pharmaceutical affordability in India. It does NOT provide medical advice, diagnosis, treatment, or clinical substitution approval.**

- Generic medicine substitution must always be evaluated and approved by a qualified registered medical practitioner (RMP) or licensed retail pharmacist.
- Jan Aushadhi Kendra stock availability must be verified directly with the dispensing pharmacy before traveling.

---

## 📄 License

MedWise is open-source software licensed under the **[MIT License](LICENSE)** (an OSI-approved permissive license).

Copyright (c) 2026 deeps0408 & MedWise Contributors.

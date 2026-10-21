# Contributing to MedLedger

First off, thank you for considering contributing to **MedLedger**! 🩺✨

Whether you are fixing a bug, expanding pharmaceutical datasets, adding tests, or refining accessibility for patients and pharmacists, your contributions directly advance healthcare affordability and price transparency in India.

This project is actively participating in **Hacktoberfest** 🎃. We welcome contributors of all experience levels, from first-time open-source participants to seasoned software engineers and pharmacists!

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Hacktoberfest Guidelines & Quality Standards](#hacktoberfest-guidelines--quality-standards)
- [Ways to Contribute](#ways-to-contribute)
- [Local Development Setup](#local-development-setup)
  - [Prerequisites](#prerequisites)
  - [1. Fork & Clone](#1-fork--clone)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [Running Automated Tests](#running-automated-tests)
- [Coding Standards & Guidelines](#coding-standards--guidelines)
  - [Python (Backend)](#python-backend)
  - [TypeScript & React (Frontend)](#typescript--react-frontend)
- [Git Conventions & Pull Request Workflow](#git-conventions--pull-request-workflow)
- [Pull Request Checklist](#pull-request-checklist)

---

## Code of Conduct

MedLedger adheres to the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct. By participating in this project, you agree to treat all community members with empathy, respect, and constructive collaboration. Harassment, discrimination, or derogatory comments will not be tolerated.

---

## Hacktoberfest Guidelines & Quality Standards

We love Hacktoberfest, but **we value meaningful, quality contributions over quantity**:

- 🚫 **No Spam or Low-Effort PRs**: PRs that merely change a single word in documentation, add arbitrary whitespace, or submit automated bot-generated churn will be labeled `spam` / `invalid` and closed immediately.
- 🎯 **Look for Issues**: Check the repository [Issues tab](https://github.com/dsy404/med-cure/issues) for issues tagged:
  - `hacktoberfest`
  - `good first issue`
  - `help wanted`
  - `clinical-data`
  - `frontend-ux`
- 💬 **Claim Before Coding**: Comment on an existing issue or open a new one proposing your feature/fix before opening a PR. This prevents duplicate effort and ensures alignment with project architecture.

---

## Ways to Contribute

Here are high-impact areas where MedLedger needs community contributions:

### 1. Expand Verified Brand Aliases 💊
- **File:** [`backend/app/services/brand_aliases.py`](backend/app/services/brand_aliases.py)
- **Task:** Add verified Indian commercial medicine brand names mapped to their active salt molecules and default strength compositions (e.g., Crocin, Augmentin, Dolo, Glycomet, Telma, Pan-D).
- **Rule:** Every alias must cite a verifiable clinical reference or official CDSCO/NPPA listing. Never fabricate formulations.

### 2. Jan Aushadhi Kendra Directory Expansion 📍
- **File:** [`backend/app/services/kendra_service.py`](backend/app/services/kendra_service.py)
- **Task:** Expand the official PMBJP (Pradhan Mantri Bhartiya Janaushadhi Pariyojana) store directory with verified addresses, postal pincodes, and latitude/longitude coordinates across underserved Indian states and rural districts.

### 3. OCR Foil Glare & Packaging Heuristics 📷
- **File:** [`backend/app/services/ocr_service.py`](backend/app/services/ocr_service.py)
- **Task:** Improve image preprocessing heuristics (adaptive thresholding, CLAHE foil de-glare, morphological deskewing) to handle low-resolution blister packs and faded clinical prints.

### 4. Frontend UI/UX & Accessibility ♿
- **Directory:** [`frontend/src/`](frontend/src/)
- **Task:**
  - Improve WCAG 2.1 AA accessibility (color contrast, screen reader labels, keyboard focus trapping).
  - Enhance mobile responsiveness across smartphone viewports.
  - Add localized UI text for regional Indian languages (Hindi, Tamil, Telugu, Bengali, Kannada, Marathi).

### 5. Automated Tests & Edge Cases 🧪
- **Directory:** [`backend/tests/`](backend/tests/)
- **Task:** Write unit and regression tests covering multi-salt combination equivalences, dosage form conversions (syrup vs suspension), and price normalization arithmetic.

---

## Local Development Setup

### Prerequisites
- **Git** installed on your system.
- **Python 3.10+** (tested up to Python 3.14).
- **Node.js 18+** & **npm 9+**.
- *(Optional)* [Ollama](https://ollama.com/) with `ollama pull gemma2:2b` if testing local AI interpretation.

### 1. Fork & Clone
Fork the repository on GitHub, then clone your fork locally:
```bash
git clone https://github.com/<your-username>/med-cure.git
cd med-cure
```

Add the upstream remote:
```bash
git remote add upstream https://github.com/dsy404/med-cure.git
```

### 2. Backend Setup
Create and activate a virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

Run the backend server:
```bash
# Windows
.\run_backend.ps1

# Or manually on any OS
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
The API documentation will be available at **`http://127.0.0.1:8000/docs`**.

### 3. Frontend Setup
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
The application will launch on **`http://localhost:5173`**.

---

## Running Automated Tests

Before submitting any code, verify that all automated tests pass:

```bash
# From the repository root
python -m pytest -v
```
*(On Windows you can also run `.\run_tests.ps1`)*

All 46+ tests should pass with 100% pass rate. If your change introduces new functionality, add corresponding unit tests under `backend/tests/`.

---

## Coding Standards & Guidelines

### Python (Backend)
- Follow **PEP 8** style guidelines.
- Use explicit type hints for all function signatures and Pydantic schemas.
- Preserve deterministic verification rules: **never guess medicine matches or hardcode fabricated prices**.
- Format code cleanly using `black` or standard PEP 8 linters.

### TypeScript & React (Frontend)
- Use strict TypeScript types (avoid `any`).
- Follow functional component architecture with React hooks.
- Keep components modular and reusable under `frontend/src/components/`.
- Ensure clean code formatting (respect `.oxlintrc.json` and project conventions).

---

## Git Conventions & Pull Request Workflow

1. **Keep your fork synchronized**:
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create a dedicated feature branch**:
   ```bash
   git checkout -b feat/add-dolo-brand-alias
   # or
   git checkout -b fix/prescription-table-mobile-wrap
   ```

3. **Follow Conventional Commits**:
   - `feat:` A new feature or dataset addition
   - `fix:` A bug fix or regression patch
   - `docs:` Documentation improvements or translations
   - `test:` Adding missing tests or refactoring test suites
   - `refactor:` Code improvements without functional changes

4. **Push your branch to your fork**:
   ```bash
   git push origin feat/add-dolo-brand-alias
   ```

5. **Open a Pull Request**:
   - Go to `https://github.com/dsy404/med-cure` and click **Compare & pull request**.
   - Provide a clear, descriptive title and explain what changes were made and why.
   - Reference any relevant issues (e.g. `Closes #12`).

---

## Pull Request Checklist

Before submitting your PR, make sure you can check all of the following:

- [ ] Code runs cleanly with no syntax errors.
- [ ] All automated tests pass (`python -m pytest -v`).
- [ ] New features include corresponding unit tests where applicable.
- [ ] No extraneous files committed (e.g. `.venv/`, `node_modules/`, `__pycache__/`, `.db`).
- [ ] Commits adhere to Conventional Commits standards.
- [ ] The PR description clearly explains the changes and references related issues.

---

Thank you for helping make healthcare transparent, verified, and affordable for millions! 🇮🇳💙

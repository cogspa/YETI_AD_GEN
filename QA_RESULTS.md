# YETI Ad Generator — Quality Assurance & Evaluation Report

**Campaign**: `yeti-la-go-anywhere-2026` ("Go Anywhere with YETI")  
**Evaluation Date**: August 18, 2026  
**Pipeline Status**: ✅ **ALL TESTS & DETERMINISTIC QUALITY CHECKS PASSING**

---

## 1. Fresh-Clone Setup Verification

The repository was verified for fresh-clone usability without external dependencies beyond standard Python 3.12 and Node.js:

| Step | Command | Result |
| :--- | :--- | :--- |
| **Virtualenv Creation** | `python3 -m venv .venv && source .venv/bin/activate` | ✅ Clean virtual environment created |
| **Python Dependencies** | `pip install -r backend/requirements.txt` | ✅ Installed FastAPI, Pillow, Pydantic, Dropbox SDK, Google GenAI |
| **Environment Config** | `cp .env.example .env` | ✅ Variable names only; zero live secrets needed for local execution |
| **Node Dependencies** | `npm --prefix frontend install` | ✅ Clean React 19 + TypeScript installation |
| **Backend Server** | `uvicorn backend.app.main:app --port 8000 --host 0.0.0.0` | ✅ FastAPI running and listening on port 8000 |
| **Frontend Server** | `npm run --prefix frontend dev -- --port 5173` | ✅ Vite dev server running on port 5173 |

---

## 2. Test Execution & Quality Gates

### A. Backend Pytest Suite (49/49 Passing)
```bash
PYTHONPATH=. .venv/bin/pytest backend/tests/ -v
```
- `backend/tests/test_asset_resolver.py` (6 tests): Canonical local resolution, Dropbox cache, path traversal rejection, corrupt image detection, missing blocking asset detection.
- `backend/tests/test_brief_validation.py` (12 tests): Schema validation, age range cross-band rejection, product targeting rules, background pool validation, tagline color constraints, directory traversal blocking.
- `backend/tests/test_compositor.py` (5 tests): Ratio layout stability, exact pixel dimensions (1080×1080, 1920×1080, 1080×1920), packshot aspect ratio retention, activity tagline color rendering.
- `backend/tests/test_concept_planner.py` (8 tests): 6 concepts × 3 formats = 18 plans, age/product targeting, background pool matching, format concept locking across ratios, seeded reproducibility, repeat protection with prior manifest.
- `backend/tests/test_gemini_generator.py` (4 tests): Guardrail prompt construction, mock background labeling, approved asset bypass (Gemini never called when approved asset exists), error handling.
- `backend/tests/test_pipeline.py` (1 test): Full end-to-end pipeline execution from brief JSON to 18 rendered ads, contact sheet, and manifest.
- `backend/tests/test_quality_checker.py` (6 tests): Secret redaction (`sl.u.*`, `AIzaSy*`, `Bearer`), valid run quality check passing (8/8 blocking rules), dimension tampering detection, age-color mismatch detection, tagline color violation detection, format locking detection.
- `backend/tests/test_storage_adapter.py` (7 tests): Local storage lifecycle, Dropbox path normalization, unconfigured status handling, token refresh lifecycle.

**Result**: `49 passed in 42.04s` (100% pass rate).

### B. Frontend Vitest Suite (3/3 Passing)
```bash
npx --prefix frontend vitest run --dir frontend
```
- `valid JSON reveals six audiences, three formats, and 18 outputs` (PASSED)
- `clicking GENERATE 18 ADS opens progress modal` (PASSED)
- `inspect / edit JSON panel expands and displays editable JSON` (PASSED)

**Result**: `3 passed in 187ms` (100% pass rate).

### C. Frontend Production Build & Typecheck
```bash
npm run --prefix frontend build
```
- TypeScript (`tsc -b`): `0 errors`.
- Vite bundle output: `dist/index.html` (0.45 kB), `dist/assets/index.css` (20.36 kB), `dist/assets/index.js` (242.97 kB).

### D. Frontend Linter
```bash
npx --prefix frontend oxlint
```
- `Found 0 warnings and 0 errors` across 21 files.

---

## 3. Security & Secret Redaction Audit

1. **Automated Secret Scan**:
   - Tracked git files scanned using regex patterns covering Dropbox tokens (`sl.u.*`), Gemini keys (`AIzaSy*`), Google OAuth tokens (`ya29.*`), and Bearer authentication headers.
   - **Finding**: Zero active secrets committed to git.
2. **Environment Template (`.env.example`)**:
   - Contains variable names only with empty placeholder values.
3. **Gitignore Exclusions (`.gitignore`)**:
   - Excludes `.env`, `.env.*`, `.cache/`, `.dropbox_cache/`, `outputs/*`, `dist/`, `.DS_Store`, `.venv/`.
4. **Path Traversal Defense**:
   - `AssetResolver` rejects any path containing `../` or leading slashes.
   - Static file server verifies requested files reside strictly within `outputs/`.
5. **Runtime Secret Redaction**:
   - Every log message in `pipeline.log` is processed through `redact_secrets()` before disk write or remote upload.

---

## 4. Deterministic Blocking Checks Verification (`BLK-01` – `BLK-08`)

| Rule ID | Check Name | Specification | Verified Status |
| :--- | :--- | :--- | :---: |
| **`BLK-01`** | **Exact Quantities** | Exactly 6 concepts and 18 outputs rendered. | ✅ **PASS** |
| **`BLK-02`** | **Exact Dimensions** | 1:1 `(1080×1080)`, 16:9 `(1920×1080)`, 9:16 `(1080×1920)`. | ✅ **PASS** |
| **`BLK-03`** | **Source Asset Integrity** | SHA-256 hashes of packshots & logos match canonical assets. | ✅ **PASS** |
| **`BLK-04`** | **Age / Product Targeting** | Age ≤ 24 (`younger`) → Orange; Age ≥ 25 (`older`) → White. | ✅ **PASS** |
| **`BLK-05`** | **Activity Background Pool** | Beach → `beach-west-coast`, Camping → `camping-la-mountains`, Tailgating → Westwood / South Central. | ✅ **PASS** |
| **`BLK-06`** | **Tagline Color Standard** | Beach → Black (`#000000`); Camping & Tailgating → White (`#FFFFFF`). | ✅ **PASS** |
| **`BLK-07`** | **Format Concept Locking** | All 3 formats per audience share identical concept & assets. | ✅ **PASS** |
| **`BLK-08`** | **Packshot Aspect Ratio** | 0.0% distortion/stretching across all resolutions. | ✅ **PASS** |

---

## 5. Visual Checks & UI Verification

- **Responsive Viewports**: Tested at `1812×986` desktop, `1024×768` tablet, and `375×812` mobile viewports.
- **Interactive Lightbox**: Full-resolution image preview with metadata badge, aspect ratio chips, and single-file download.
- **Contact Sheet Modal**: Master 6 Audience Rows × 3 Format Columns grid viewable in browser and downloadable as `contact-sheet.jpg`.
- **Quality Report Modal**: Dedicated modal presenting the 8-point blocking checklist, per-audience audit metrics, and download links for `generation-report.json` and `pipeline.log`.
- **Keyboard & Accessibility**: Focus rings visible on all interactive elements, modal `Escape` key listeners, and ARIA labels.

---

## 6. Honest Limitations & Constraints

1. **No Automated Trademark Detection**:
   - The system does not claim automated trademark detection. Background validation is strictly bounded to approved asset pool verification and deterministic color/aspect-ratio compliance.
2. **AI Scene Fallback Bounding**:
   - Gemini background generation is invoked **only** when an approved background file is physically missing from local storage and Dropbox cache. When all canonical assets are present, Gemini is never called.
3. **Repeat Protection Pool Exhaustion**:
   - When an asset pool has fewer unique assets than audiences (e.g. 2 camping backgrounds for 3 camping audiences), the system gracefully reuses an approved asset and logs a deterministic warning note rather than aborting the pipeline.
4. **Storage Graceful Degradation**:
   - When Dropbox credentials are not configured or network requests fail, the pipeline falls back to local storage in `outputs/` without failing the generation run.

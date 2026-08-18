# YETI Los Angeles Multi-Format Creative Ad Generator (2026)

A deterministic, high-throughput creative advertising adaptation pipeline for YETI's **"Go Anywhere with YETI"** campaign. Built with **FastAPI**, **Pillow (PIL)**, **React 19**, **TypeScript**, and **Vanilla CSS**.

Generates **18 deterministic, brand-compliant ad adaptations** across **6 audience segments** and **3 aspect ratios** (`1:1` Instagram Post, `16:9` Landscape Display, `9:16` Story/Reel) with pixel-perfect composition, typography, and controlled asset locking.

---

## ⚡ Quick Start (Fresh Clone Setup)

### 1. Prerequisites
- **Python**: `3.12+`
- **Node.js**: `18+`
- **npm**: `9+`

### 2. Backend Setup
```bash
# 1. Clone repository
git clone https://github.com/cogspa/YETI_AD_GEN.git
cd YETI_AD_GEN

# 2. Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Configure environment (variable names only, no secrets required for local generation)
cp .env.example .env

# 5. Start FastAPI Backend (Port 8000)
uvicorn backend.app.main:app --port 8000 --host 0.0.0.0 --reload
```

### 3. Frontend Setup
```bash
# In a new terminal window:
cd frontend
npm install
npm run dev -- --port 5173
```

Open **`http://localhost:5173`** in your browser.

---

## 🧪 Running Automated Tests

```bash
# Run all 49 backend unit and integration tests
PYTHONPATH=. .venv/bin/pytest backend/tests/ -v

# Run frontend Vitest test suite
npx --prefix frontend vitest run --dir frontend

# Run frontend typecheck and production build
npm run --prefix frontend build

# Run frontend linter
npx --prefix frontend oxlint
```

---

## 🏗️ Architecture & Pipeline Flow

```
Campaign Brief (JSON)
        │
        ▼
[1] Brief Validation (Pydantic + JSON Schema)
        │
        ▼
[2] Asset Resolver (Local Canonical Assets + Dropbox Cloud Cache)
        │
        ▼
[3] Concept Planner (Deterministic Seeded Randomization & Repeat Protection)
        │  ├── Enforces Age ≤ 24 → Orange Cooler (Product Model 1)
        │  ├── Enforces Age ≥ 25 → White Cooler (Product Model 2)
        │  ├── Locks 1:1, 16:9, 9:16 to identical concept/background/product/tagline
        │  └── Enforces Beach → Black Tagline; Camping/Tailgating → White Tagline
        ▼
[4] Composite Renderer (PIL Bicubic Scaler + Ratio Layout Configs)
        │  ├── 1:1 Square (1080×1080)
        │  ├── 16:9 Landscape (1920×1080)
        │  └── 9:16 Vertical Story (1080×1920)
        ▼
[5] Contact Sheet Generator (6 Audiences × 3 Formats Master Grid)
        │
        ▼
[6] Deterministic Quality Checker (8/8 Blocking Rules + Secret Redaction)
        │  ├── Emits generation-report.json
        │  └── Emits secret-safe pipeline.log (JSONL)
        ▼
[7] Storage Adapter (Local filesystem fallback or Dropbox API)
```

---

## 🛡️ Deterministic Blocking Rules (`BLK-01` – `BLK-08`)

1. **`BLK-01`**: Exactly 6 audience concepts planned and 18 output images rendered.
2. **`BLK-02`**: Exact pixel dimensions: `1080×1080` (1:1), `1920×1080` (16:9), `1080×1920` (9:16).
3. **`BLK-03`**: Source asset SHA-256 integrity verification against canonical assets.
4. **`BLK-04`**: Strict age targeting: Younger (≤ 24) receives Orange Cooler; Older (≥ 25) receives White Cooler.
5. **`BLK-05`**: Activity background pool mapping (Beach → `beach-west-coast`, Camping → `camping-la-mountains`, Tailgating → Westwood / South Central).
6. **`BLK-06`**: Tagline color standard: Beach uses Black `#000000`; Camping & Tailgating use White `#FFFFFF`.
7. **`BLK-07`**: Format concept locking: All 3 formats for each audience share the identical concept, background scene, product, and tagline.
8. **`BLK-08`**: Packshot aspect ratio retention: 0.0% distortion/stretching across all resolutions.

---

## 🔒 Security & Safe Credentials

- **Zero Committed Secrets**: All Dropbox tokens (`sl.u.*`), Gemini keys (`AIzaSy*`), and authorization headers are strictly excluded from git and dynamically redacted in all runtime logs (`pipeline.log`).
- **Restricted Local CORS**: CORS is restricted to local origin `http://localhost:5173`.
- **Path Traversal Protection**: All asset resolution and output serving endpoints sanitize paths and block `../` directory escapes.

---

## 📦 Output Artifacts Per Generation Run

Outputs are saved in `outputs/<campaignId>/runs/<runId>/` and uploaded to Dropbox if configured:
- `outputs/<AudienceId>/<Format>/<Filename>.png` (18 PNG ad adaptations)
- `contact-sheet.jpg` (6×3 master visual review grid)
- `generation-report.json` (Automated compliance and quality audit)
- `pipeline.log` (Secret-redacted JSONL execution trace)
- `generation-manifest.json` (Seeded provenance manifest)
- `<campaignId>-<runId>-all-ads.zip` (Complete downloadable package)

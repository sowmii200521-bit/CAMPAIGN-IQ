# 📡 CampaignIQ: REST API Reference

The CampaignIQ backend exposes a REST API powered by Flask, providing endpoints for causal dataset ingestion, double-robust econometric execution, grounded AI analysis, and artifact retrieval.

---

## Base URL Configuration

* **Local Development:** `http://127.0.0.1:5000` (Reverse-proxied by Vite to `/api`)
* **Vercel Production:** `https://your-deployment.vercel.app/api` (via `vercel.json` rewrites)
* **Custom Backend Host:** Configured via `VITE_API_BASE_URL` in frontend environment

---

## Endpoints

### 1. Health Check
Checks service availability and operational readiness.

* **Endpoint:** `GET /api/health`
* **Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "CampaignIQ Causal Engine API",
  "version": "1.0.0"
}
```

---

### 2. Download Demo Dataset
Returns the bundled 3,000+ row benchmark CSV dataset (`campaign_dataset.csv`) for testing and demonstration purposes.

* **Endpoint:** `GET /api/demo_dataset`
* **Response (200 OK):** File stream (`text/csv`, attachment filename: `campaign_dataset.csv`)

---

### 3. Execute Causal Analysis
Uploads an observational campaign CSV, runs the 5-fold cross-fitted AIPW econometric engine, and returns session metrics and file manifests.

* **Endpoint:** `POST /api/analyze`
* **Content-Type:** `multipart/form-data`
* **Request Body:**
  * `file` (File, required): CSV file containing treatment, outcome, and demographic/behavioral covariates.

* **Response (200 OK):**
```json
{
  "status": "success",
  "runId": "ffe96861-53ed-4752-afe1-8c4961d837af",
  "stats": {
    "ate": 0.0511,
    "confidence": 0.95,
    "ci_lower": 0.0241,
    "ci_upper": 0.0780,
    "naive_difference": 0.0673,
    "sample_size": 2000
  },
  "results": [
    {
      "name": "Causal Impact Summary",
      "fileName": "causal_impact_summary.csv",
      "fileType": "csv",
      "description": "Population ATE, naive comparison, and confidence intervals"
    },
    {
      "name": "Next Wave Recommendations",
      "fileName": "next_wave_recommendations_aipw.csv",
      "fileType": "csv",
      "description": "CATE subgroup rankings for future budget allocation"
    },
    {
      "name": "Covariate Balance (Love Plot)",
      "fileName": "love_plot.png",
      "fileType": "png",
      "description": "Pre vs. post weighting Standardized Mean Differences (SMD)"
    },
    {
      "name": "Propensity Score Overlap",
      "fileName": "propensity_overlap.png",
      "fileType": "png",
      "description": "Common support distribution between treated and control cohorts"
    },
    {
      "name": "Executive Summary Report",
      "fileName": "report.md",
      "fileType": "md",
      "description": "Synthesized C-suite briefing and strategic guidance"
    }
  ]
}
```

* **Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Invalid file type. Only CSV allowed."
}
```

---

### 3. Grounded AI Analyst Copilot
Submits user queries to the data-grounded AI Copilot. Context is strictly extracted from the active session artifacts.

* **Endpoint:** `POST /api/chat`
* **Content-Type:** `application/json`
* **Request Body:**
```json
{
  "runId": "ffe96861-53ed-4752-afe1-8c4961d837af",
  "message": "What was our true causal uplift vs naive correlation?",
  "history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hello! I am your CampaignIQ AI Analyst."
    }
  ]
}
```

* **Response (200 OK):**
```json
{
  "status": "success",
  "answer": "Based on your verified run artifacts (Session #ffe96861):\n• Naive Correlational Uplift: +6.73 percentage points.\n• True Causal Impact (AIPW ATE): +5.11 percentage points (95% CI: [2.41%, 7.80%]).\n• The 1.62pp Phantom Gap: Unadjusted analytics credited the campaign for natural conversions. Confounder weighting adjusted for prior engagement (-0.303 SMD) and district imbalances, driving post-weighting SMD < 0.01.",
  "runId": "ffe96861-53ed-4752-afe1-8c4961d837af"
}
```

---

### 4. Download Single Artifact
Retrieves a specific output artifact (CSV, PNG, or Markdown) by session ID.

* **Endpoint:** `GET /api/download/<run_id>/<file_name>`
* **Parameters:**
  * `run_id` (string, required): The UUID of the analysis session.
  * `file_name` (string, required): e.g., `causal_impact_summary.csv`, `love_plot.png`.
* **Response:** Raw file binary with appropriate `Content-Type` (`text/csv`, `image/png`, `text/markdown`).

---

### 5. Download All Artifacts (ZIP Bundle)
Bundles all session artifacts into a single compressed ZIP archive.

* **Endpoint:** `GET /api/download_all/<run_id>`
* **Parameters:**
  * `run_id` (string, required): The UUID of the analysis session.
* **Response:** `application/zip` archive containing all CSVs, plots, and markdown reports.

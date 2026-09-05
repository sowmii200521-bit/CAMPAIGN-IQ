# 🚀 CampaignIQ: Deployment Guide (Vercel & Production Cloud)

This guide covers deploying the full-stack CampaignIQ platform—including the React/TypeScript frontend on **Vercel** and the Python Causal/AI backend on **Render, Railway, or Vercel Serverless**.

---

## 1. Quick Deploy: Frontend on Vercel

### Option A: 1-Click Deploy via Vercel Dashboard (Recommended)
1. Push your repository to GitHub: `https://github.com/sowmii200521-bit/CAMPAIGN-IQ`.
2. Go to **[vercel.com/new](https://vercel.com/new)** and import your repository.
3. Vercel automatically detects the root `vercel.json` configuration:
   * **Framework Preset:** `Vite`
   * **Root Directory:** `./` (or select `v1`)
   * **Build Command:** `cd v1 && npm install && npm run build` (or `npm run build` if Root is `v1`)
   * **Output Directory:** `v1/dist` (or `dist` if Root is `v1`)
4. In **Environment Variables**, add:
   * `VITE_API_BASE_URL`: URL of your deployed Python backend (e.g., `https://campaigniq-api.onrender.com` or leave blank if using Vercel rewrites).
5. Click **Deploy**. Your frontend will be live with global CDN, SSL, and instant rollbacks!

---

### Option B: Deploy via Vercel CLI
```bash
# 1. Install Vercel CLI globally
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy from the project root
vercel --prod
```

---

## 2. Deploying the Python Causal Backend

The Python backend executes 5-fold cross-fitting and calls Hugging Face serverless inference. It can be hosted on any container or cloud provider:

### Deploy to Render (Free & Instant)
1. Create an account on **[render.com](https://render.com)**.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository: `CAMPAIGN-IQ`.
4. Configure settings:
   * **Root Directory:** `v1/backend`
   * **Environment:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app -b 0.0.0.0:$PORT --timeout 120`
5. Under **Environment Variables**, add:
   * `HF_TOKEN`: Your Hugging Face fine-grained token (with Inference API permissions).
6. Click **Create Web Service**. Copy your live service URL (e.g., `https://campaigniq-api.onrender.com`).
7. Update `VITE_API_BASE_URL` in your Vercel frontend to point to this Render URL!

---

### Deploy to Railway
```bash
# 1. Install Railway CLI
npm install -g @railway/cli
railway login

# 2. Initialize and deploy
cd v1/backend
railway init
railway up
```

---

## 3. Environment Variables Reference

| Variable | Location | Description |
| :--- | :--- | :--- |
| `HF_TOKEN` | Backend (`.env` or Cloud Provider) | Hugging Face fine-grained API token for Meta-Llama-3.1-8B copilot. |
| `VITE_API_BASE_URL` | Frontend (`.env` or Vercel Settings) | URL of the backend API. Defaults to relative `/api` (works with local Vite proxy and Vercel rewrites). |
| `PORT` | Backend (Cloud Provider) | Port for Flask/Gunicorn (auto-injected by Render/Railway, defaults to 5000). |

---

## 4. Local Development Setup

To run both frontend and backend locally on your machine:

```powershell
# 1. Start Python Backend (Terminal 1)
cd v1/backend
.\venv\Scripts\python.exe app.py
# Backend runs on http://127.0.0.1:5000

# 2. Start Vite Frontend (Terminal 2)
cd v1
npm install
npm run dev
# Frontend runs on http://localhost:8080 (reverse-proxies /api to 127.0.0.1:5000)
```

---

## 5. Verifying Deployment Health

Once deployed, verify your API health endpoint:
```bash
curl https://<YOUR_BACKEND_URL>/api/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "CampaignIQ Causal Engine API",
  "version": "1.0.0"
}
```

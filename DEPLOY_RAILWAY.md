# 🚆 Viaggio Italia — Railway Deployment Guide

This guide walks you through deploying the **Viaggio Italia Travel Planner & Maps MCP** application to [Railway.app](https://railway.app/).

---

## ⚡ Quick Deployment (GitHub Connection - 2 Minutes)

### Step 1: Push Project to GitHub
Initialize and push your repository to GitHub:
```bash
git init
git add .
git commit -m "Deploy Viaggio Italia to Railway"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/italy-travel-planner.git
git push -u origin main
```

### Step 2: Create Project on Railway
1. Navigate to **[Railway.app](https://railway.app/)** and sign in with GitHub.
2. Click **"+ New Project"**.
3. Select **"Deploy from GitHub repo"**.
4. Choose your repository: `italy-travel-planner`.

### Step 3: Configure Environment Variables
In your Railway project service dashboard, click on the **"Variables"** tab and add:

| Variable Name | Value | Description |
|---|---|---|
| `GROQ_API_KEY` | `your_groq_api_key_here` | High-speed LLM engine for live itinerary mutations |
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | Multi-modal travel synthesis & verified grounding |
| `PYTHONUNBUFFERED` | `1` | Real-time container log streaming |

*(Note: Railway automatically injects and manages the `PORT` variable).*

### Step 4: Generate Public Domain & Launch
1. In your service dashboard, go to **"Settings"** → **"Networking"**.
2. Click **"Generate Domain"** (e.g. `viaggio-italia-production.up.railway.app`).
3. Click the generated URL to access your live production application!

---

## 🛠️ Alternative: Deploy via Railway CLI

If you prefer deploying directly from your terminal using the Railway CLI:

```bash
# 1. Install Railway CLI
npm install -g @railway/cli   # or: brew install railway

# 2. Login to your account
railway login

# 3. Initialize and link project
railway init

# 4. Set Environment Variables
railway variables set GROQ_API_KEY="your_groq_api_key_here"
railway variables set GEMINI_API_KEY="your_gemini_api_key_here"
railway variables set PYTHONUNBUFFERED="1"

# 5. Deploy the container
railway up

# 6. Generate public domain
railway domain
```

---

## 🔍 Verification & Health Check

Your deployed Railway service will automatically run health checks on:
```
GET /api/health
```
Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "engine": "Hybrid Groq + Gemini AI Travel Agent & Maps MCP",
  "llm_provider": "Groq + Gemini",
  "groq_connected": true,
  "gemini_connected": true,
  "mcp_tools_count": 9
}
```

---

## 📦 Included Configuration Files
- `Dockerfile`: Lightweight Python 3.11-slim container with automated healthcheck.
- `railway.json`: Native Railway deployment and restart policy schema.
- `Procfile`: Multi-cloud buildpack compatibility (`web: python3 web/app.py`).
- `requirements.txt`: Zero-bloat, Python standard library-powered setup.
- `.dockerignore`: Context exclusions for ultra-fast builds.

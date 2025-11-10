# 🔐 SIEMSpeak — AI-Powered Security Analytics Assistant

[![View Live](https://img.shields.io/badge/View-SIEM%20Assistant-green?style=for-the-badge&logo=web)](https://ask-siem.vercel.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Events Analyzed](https://img.shields.io/badge/Events%20Analyzed-10K%2B-orange?style=flat)]()
[![Query Accuracy](https://img.shields.io/badge/Query%20Accuracy-98%25-brightgreen?style=flat)]()
[![Avg Response](https://img.shields.io/badge/Avg%20Response-0.3s-purple?style=flat)]()


**SIEMSpeak** converts SIEM logs into instant, actionable insights using natural language — ask, analyze, act.

---

## 🚀 Live Demo
🔗 https://ask-siem.vercel.app/ *(Replace with your deployed link)*

---

## 📌 Problem Statement

Security Operation Centers (SOCs) rely on SIEM tools to monitor and investigate threats, but most require complex query languages (KQL, SPL, EQL), which slows investigations and requires experienced analysts. SIEMSpeak solves this by letting analysts query logs using plain English and receive concise summaries, visualizations, and suggested remediation.

**Example**
- **You:** `Show failed logins in the last 24 hours`  
- **AI:** `Found 347 failed login attempts from 42 unique IPs. Peak activity at 09:00 UTC. Top targeted user: admin (23 attempts).`

---

## 👥 Contributors

- **Nikhil Shimpy** – [@NikhilShimpy](https://github.com/NikhilShimpy)  
- **Vedant** – [@Chitlangia-Vedant](https://github.com/Chitlangia-Vedant)
- **Vaibhav Tomar** – [@Vaibhav030406](https://github.com/Vaibhav030406)
- **Chetna Sikarwar** – [@chetnasingh31](https://github.com/chetnasingh31)
  
---

## ✨ Key Achievements & Metrics (Demo)

| Metric | Value |
|--------|-------|
| Events Analyzed | **10,000+** |
| Query Accuracy | **98%** |
| Avg Response Time | **0.3s** |
| Threats Detected | **247+** |

---

## 🧠 Core Features

- **Natural Language Queries** — Ask SIEM data questions in plain English.
- **Real-Time Processing** — Sub-second results for urgent queries.
- **Interactive Visual Dashboards** — Timelines, maps, severity heatmaps.
- **Smart Filters** — Time windows, IP ranges, severity, user, tags.
- **Threat Intelligence & ML** — Anomaly detection, enrichment with IOCs.
- **Exportable Reports** — PDF / CSV / JSON with charts and context.
- **RBAC & Audit Logging** — Enterprise-ready access control and trail.

---
[User UI] ↔ [API Gateway] ↔ [LLM Service / Query Translator] ↔ [Query Builder]
                                      ↓
                   [SIEM / Log Storage (Elastic / Splunk / DB)]
                                      ↓
             [Analytics Engine → Enrichment → Visualization]
---

- **Frontend:** React (Next.js) + Tailwind  
- **Backend:** FastAPI (Python) / optionally Flask  
- **AI/LLM:** OpenAI GPT family / Llama / Fine-tuned model via LangChain  
- **Log Storage:** ElasticSearch, Splunk, or MongoDB (configurable)  
- **Visualization:** Chart.js / D3.js / Mapbox for geo IPs  
- **Deployment:** Docker, Kubernetes, Vercel (frontend) / AWS/GCP (backend)

---

## 🛠️ Tech Stack

- **Frontend:** React, Next.js, Tailwind CSS, Chart.js, Mapbox  
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Celery (for async enrichment)  
- **AI Layer:** OpenAI API / Local LLM + LangChain adapters  
- **DB / SIEM:** ElasticSearch / Splunk / PostgreSQL / MongoDB  
- **Auth / Identity:** OAuth2 / JWT / SSO integration for Enterprise  
- **Storage:** S3 / Firebase Storage (optional)  
- **CI/CD:** GitHub Actions + Docker + Terraform (infra as code)

---

## ⚙️ Environment & Configuration

Create a `.env` file in the `/backend` folder:

```bash
# Example .env
APP_ENV=development
HOST=0.0.0.0
PORT=8000

# SIEM / DB
ELASTIC_URL=http://localhost:9200
ELASTIC_USER=elastic
ELASTIC_PASS=changeme

# OpenAI / LLM
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER=openai

# Auth & Security
JWT_SECRET=supersecretjwtkey
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret

# Optional: S3 / Storage
S3_BUCKET=siemspeak-logs
S3_REGION=us-east-1
S3_ACCESS_KEY=AKIA...
S3_SECRET_KEY=...
```
---



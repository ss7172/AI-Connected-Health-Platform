# Connected Health Platform

A 3-layer clinical platform: Patient Management System → Data Pipeline → AI Assistant. One codebase, one database, one deployment.

**Live Demo:** [https://redmond-pms-frontend.onrender.com](https://redmond-pms-frontend.onrender.com)

> ⚠️ Hosted on Render free tier — first load may take ~50 seconds to spin up.

---

## Demo Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | `admin` | `admin123` | Full access: Dashboard, Pipeline, AI Assistant, all management |
| Doctor | `dr.mohanty` | `doctor123` | Today's schedule, clinical notes, AI Assistant |
| Front Desk | `frontdesk1` | `front123` | Patient registration, appointment booking, billing |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  React 18 · Role-based UI · Recharts · Chat Interface       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                      API LAYER                               │
│  Flask · JWT Auth · Marshmallow Validation · 35+ Endpoints   │
└──────┬──────────────────┬───────────────────┬───────────────┘
       │                  │                   │
┌──────┴──────┐  ┌────────┴────────┐  ┌──────┴──────────────┐
│     PMS     │  │    PIPELINE     │  │   AI ASSISTANT      │
│  9 tables   │  │  4 ETL jobs     │  │  RAG over 7,631     │
│  30+ APIs   │  │  20K+ rows      │  │  patient summaries  │
│  10K pts    │  │  APScheduler    │  │  Claude Haiku       │
└──────┬──────┘  └────────┬────────┘  └──────┬──────────────┘
       │                  │                   │
┌──────┴──────────────────┴───────────────────┴───────────────┐
│                    PostgreSQL 15                              │
│  9 PMS tables · analytics schema (5 tables) · pgvector       │
└─────────────────────────────────────────────────────────────┘
```

**Data flows in one direction:** PMS captures clinical data → Pipeline transforms it into analytics tables and patient summaries → AI Assistant embeds summaries and answers natural language queries over them.

---

## Layer 1: Patient Management System

Full-stack clinic management handling the daily workflow of an Indian polyclinic.

### Features

**Role-Based Access Control** — Admin gets full access. Doctors see their schedule and write clinical notes. Front desk handles registration, booking, and billing.

**Patient Management** — Phone-based deduplication (Indian patients reliably have mobile numbers, email is optional). Search across 10,000+ patients with real-time filtering. Paginated lists.

**Appointment Scheduling** — Cascading dropdowns: department → doctor → date → available 30-minute slots (9 AM–5 PM). Double-layered conflict detection: application-level check for human-readable errors + database unique constraint for race condition protection.

**Status Transitions with Role Enforcement:**
- `scheduled → in_progress` (doctor only)
- `scheduled → cancelled / no_show` (front desk, admin)
- `in_progress → completed` (doctor only, triggers visit creation)

**Clinical Documentation** — Doctors record symptoms, diagnosis (with ICD-10 code), prescription, and follow-up. Visit creation auto-completes the appointment and auto-creates a billing record in a single transaction.

**Billing** — Auto-generated consultation fee on visit creation (fee is department-level, not doctor-level — Indian polyclinic model). Front desk adds test/procedure line items. Total recalculates from line items on every change. Payment via cash, card, UPI, or insurance.

**Admin Dashboard** — Today's appointments, revenue, pending payments. 30-day revenue chart (consultation vs tests/procedures breakdown). Department performance table.

### Data Model

9 PostgreSQL tables:

```
users
departments         ← consultation_fee is department-level
doctors             ← linked 1-to-1 with users
patients            ← phone is primary dedup key
appointments        ← unique constraint on (doctor_id, date, time)
visits              ← one per appointment, auto-creates billing
billing_records     ← invoice header
billing_items       ← line items (consultation fee + tests/procedures)
patient_documents   ← file metadata
```

8 custom indexes beyond PKs and unique constraints — composite indexes for high-frequency query patterns. Query performance verified with `EXPLAIN ANALYZE`:

| Query | Index Used | Time |
|-------|-----------|------|
| Patient phone lookup | `ix_patients_phone` | 0.13ms |
| Doctor schedule | `ix_appointments_doctor_date` | 0.10ms |

---

## Layer 2: Clinical Data Pipeline

4 ETL jobs that transform PMS operational data into pre-computed analytics tables. Replaces real-time aggregation queries with materialized views.

### Jobs

| Job | Output Table | Rows | Duration |
|-----|-------------|------|----------|
| `revenue_analytics` | `analytics.daily_revenue` | 1,461 | ~1s |
| `operational_metrics` | `analytics.operational_metrics` | 1,520 | ~1s |
| `patient_analytics` | `analytics.patient_profiles` | 10,003 | ~4s |
| `clinical_summaries` | `analytics.patient_clinical_summaries` | 7,631 | ~20s |

**Total: 20,615 rows in ~25 seconds.**

### Architecture Decisions

**SQL-first transforms** — Jobs 1, 3, and 4 are pure SQL with CTEs, window functions (LAG for visit frequency, ROW_NUMBER for primary doctor/department), FILTER clauses, and UPSERT (ON CONFLICT DO UPDATE). Job 2 uses SQL extraction + Python text assembly.

**APScheduler over Airflow** — 4 jobs don't justify Airflow's infrastructure overhead. APScheduler runs nightly at 2 AM as a background thread in the Flask process.

**Same PostgreSQL, analytics schema** — Logical isolation without a separate database. All pipeline output lives in the `analytics` schema alongside the PMS tables in `public`.

**Idempotent UPSERT** — Every job is safe to re-run. ON CONFLICT DO UPDATE ensures no duplicates.

### Clinical Summaries (RAG Corpus)

The `clinical_summaries` job produces structured text per patient — the input corpus for the AI Assistant:

```
PATIENT: Ramesh Nayak | Age: 50 | Gender: Male | Blood Group: B+

VISIT 1 [2026-01-15]
Dr. Rajesh Mohanty, Cardiology
Symptoms: Chest pain and shortness of breath
Diagnosis: Stable angina (ICD-10: I20.9)
Prescription: Tab. Metoprolol 25mg BD, Tab. Aspirin 75mg OD
Tests/Procedures: Cardiology Consultation (INR 500), ECG (INR 200)
Billing: INR 700 (paid via cash)
Follow-up: 2026-01-29
```

Format is intentionally flat text, not JSON — LLMs retrieve better from natural-language structured text. The RAG system chunks on `VISIT N [date]` boundaries.

### Pipeline Status Page

Admins can monitor all 4 jobs from the UI: row counts, durations, last run timestamps, and a "Run Pipeline Now" button for manual triggers.

---

## Layer 3: Clinical AI Assistant (RAG)

Natural language query interface over 7,631 patient clinical summaries. Type a clinical question, get a grounded answer from real patient data.

### How It Works

```
User query: "What medications is Ramesh Nayak on?"
     │
     ├── 1. Name detection → metadata pre-filter (ILIKE on patient_name)
     │   OR
     ├── 1. Embed query via Voyage AI (voyage-3-lite, 512-dim)
     │   2. Cosine similarity search in pgvector (top_k × 3)
     │   3. De-duplicate by patient_id (keep highest score per patient)
     │
     ├── 4. Inject retrieved chunks into grounding system prompt
     ├── 5. Claude Haiku synthesizes answer constrained to provided records
     │
     └── Response: "Ramesh Nayak is on Tab. Metoprolol 25mg BD and
                    Tab. Aspirin 75mg OD, prescribed by Dr. Rajesh Mohanty
                    for stable angina..."
         Sources: [Ramesh Nayak #1 · Cardiology]
```

### Provider Abstraction

Three abstract base classes ensure every component is swappable:

| Interface | v1 Implementation | Swap Target |
|-----------|-------------------|-------------|
| `LLMProvider` | Claude Haiku (Anthropic API) | Ollama (local models) |
| `EmbeddingProvider` | Voyage AI (voyage-3-lite) | sentence-transformers (local) |
| `VectorStore` | pgvector (PostgreSQL) | ChromaDB, Pinecone |

Switching providers is a config change (`RAG_LLM_PROVIDER=ollama` in `.env`), not an application rewrite.

### Why pgvector Over ChromaDB

ChromaDB writes to local disk. Render's free tier has an ephemeral filesystem — every restart wipes it. pgvector lives in the same PostgreSQL database as the PMS, surviving restarts without re-ingestion. One less dependency, one less failure mode.

Auto-ingestion detection on the `/query` endpoint: if pgvector is empty (first deploy), trigger ingestion before answering.

### Why Per-Visit Chunking

The pipeline produces text with natural `VISIT N [date]` boundaries. Each visit is a semantically complete unit: one doctor, one diagnosis, one prescription, one billing event. Per-visit chunks keep this coherence. Fixed-size chunks would split mid-visit and lose meaning.

Patient header is prepended to every chunk so each stands alone — the retrieval system doesn't need to fetch the patient context separately.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, Flask 3.x, SQLAlchemy 2.x, Flask-Migrate, Flask-JWT-Extended, Marshmallow |
| Frontend | React 18, React Router 7, Recharts, Vanilla CSS-in-JS |
| Database | PostgreSQL 15, pgvector |
| AI/ML | Anthropic Claude Haiku (synthesis), Voyage AI voyage-3-lite (embeddings) |
| Pipeline | APScheduler, SQL (CTEs, window functions, UPSERT) |
| Deployment | Render (backend + frontend + PostgreSQL), Gunicorn |

---

## API Overview

### Auth
```
POST   /api/v1/auth/login
GET    /api/v1/auth/me
```

### Patients
```
GET    /api/v1/patients?search=&page=&per_page=
POST   /api/v1/patients
GET    /api/v1/patients/:id
PUT    /api/v1/patients/:id
GET    /api/v1/patients/check-phone/:phone
GET    /api/v1/patients/:id/visits
```

### Appointments
```
GET    /api/v1/appointments/today
POST   /api/v1/appointments
PATCH  /api/v1/appointments/:id/status
GET    /api/v1/doctors/:id/available-slots?date=
```

### Clinical
```
POST   /api/v1/visits
GET    /api/v1/visits/:id
```

### Billing
```
GET    /api/v1/billing?status=&page=&per_page=
GET    /api/v1/billing/:id
POST   /api/v1/billing/:id/items
DELETE /api/v1/billing/:id/items/:item_id
PATCH  /api/v1/billing/:id/pay
```

### Dashboard
```
GET    /api/v1/dashboard/summary
GET    /api/v1/dashboard/revenue?period=30days
GET    /api/v1/dashboard/department-stats
```

### Pipeline
```
POST   /api/v1/pipeline/run
GET    /api/v1/pipeline/status
```

### AI Assistant
```
POST   /api/v1/assistant/query
POST   /api/v1/assistant/ingest
GET    /api/v1/assistant/status
```

---

## Local Development

### Prerequisites
- Python 3.12+
- PostgreSQL 15 (with pgvector extension)
- Node.js 18+

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://localhost/redmond_pms
ANTHROPIC_API_KEY=your-anthropic-key
VOYAGE_API_KEY=your-voyage-key
```

```bash
createdb redmond_pms
psql redmond_pms -c "CREATE EXTENSION IF NOT EXISTS vector;"
export FLASK_APP=run.py
flask db upgrade
python seed.py
python generate_data.py          # 10K patients, 22K appointments, 12K visits
python -m pipeline.runner all    # Build analytics tables + clinical summaries
python -m rag.ingestion          # Embed summaries into pgvector
flask run --port 8000
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:8000/api/v1
```

```bash
npm start
```

App runs at `http://localhost:3000`.

---

## Project Structure

```
pms/
├── backend/
│   ├── app/
│   │   ├── models/            # 9 SQLAlchemy models
│   │   ├── routes/            # 11 Blueprint route groups (incl. pipeline, assistant)
│   │   ├── services/          # Business logic layer
│   │   ├── schemas/           # Marshmallow validation
│   │   └── utils/             # Decorators, helpers, file storage
│   ├── pipeline/
│   │   ├── jobs/              # 4 ETL jobs (BaseJob + revenue/ops/patient/clinical)
│   │   ├── sql/               # Raw SQL transforms (CTEs, window functions, UPSERT)
│   │   ├── runner.py          # CLI runner + run_all orchestrator
│   │   └── scheduler.py       # APScheduler nightly cron
│   ├── rag/
│   │   ├── providers/
│   │   │   ├── base.py        # LLMProvider, EmbeddingProvider, VectorStore ABCs
│   │   │   ├── claude_provider.py
│   │   │   ├── voyage_provider.py
│   │   │   └── pgvector_store.py
│   │   ├── ingestion.py       # Summaries → chunks → embeddings → pgvector
│   │   ├── retrieval.py       # Query → embed → search → de-duplicate
│   │   ├── synthesis.py       # Chunks + query → Claude → grounded answer
│   │   └── assistant.py       # Orchestrator: retrieve → synthesize
│   ├── migrations/
│   ├── seed.py
│   ├── generate_data.py       # 10K synthetic patient generator
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/               # JWT-aware fetch wrapper
        ├── context/           # Auth context
        └── components/
            ├── auth/          # Login
            ├── common/        # Navbar, ProtectedRoute
            ├── dashboard/     # Dashboard + RevenueChart
            ├── patients/      # List, Form, Profile
            ├── appointments/  # TodaySchedule, BookAppointment
            ├── visits/        # VisitForm
            ├── billing/       # BillingList, InvoiceDetail
            ├── pipeline/      # PipelineStatus
            └── assistant/     # ChatAssistant
```

---

## Architecture Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Phone as patient dedup key | Not email | Tier 2 Indian city patients reliably have mobile numbers. Email is optional. |
| Auto-billing on visit creation | Single transaction | Visit + appointment status + billing record + consultation fee item — all commit or all rollback. |
| pgvector over ChromaDB | Same PostgreSQL | Render ephemeral filesystem kills ChromaDB on restart. pgvector persists. |
| Voyage API over sentence-transformers | No PyTorch dependency | sentence-transformers pulls ~800MB of PyTorch. Voyage is a lightweight API call. |
| Per-visit chunking | Natural boundaries | Each visit is semantically complete. Fixed-size chunks split mid-visit. |
| APScheduler over Airflow | 4 jobs | Airflow's infrastructure overhead isn't justified for 4 jobs running in 25 seconds. |
| SQL-first pipeline | CTEs + UPSERT | Pipeline transforms are set operations. Python loops would be slower and harder to debug. |

---

## Built By

Satyabrat Srikumar — Columbia University MS in Computer Science

Built as a portfolio project demonstrating technical product management and full-stack AI engineering.

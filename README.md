# Redmond Polyclinic — Patient Management System

A full-stack internal clinic management system built for Redmond Polyclinic and Diagnostic, a multi-specialty clinic in Cuttack, India. Handles patient registration, appointment scheduling, clinical documentation, billing, and an admin dashboard.

**Live Demo:** https://redmond-pms-frontend.onrender.com

> ⚠️ Hosted on Render free tier — first load may take ~50 seconds to spin up.

---

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Doctor | `dr.mohanty` | `doctor123` |
| Front Desk | `frontdesk1` | `front123` |

---

## Tech Stack

**Backend**
- Python / Flask 3.x
- SQLAlchemy 2.x + Flask-Migrate (Alembic)
- Flask-JWT-Extended (JWT auth)
- Marshmallow (request validation)
- PostgreSQL 15
- Gunicorn (production server)

**Frontend**
- React 18
- React Router 6
- Recharts (revenue chart)
- Vanilla CSS-in-JS (no framework)

**Infrastructure**
- Render (backend + frontend + PostgreSQL)
- GitHub (version control)

---

## Features

### Role-Based Access Control
Three roles with different permissions:
- **Admin** — full access including dashboard, all patient/billing management
- **Doctor** — today's schedule, clinical notes, patient visit history
- **Front Desk** — patient registration, appointment booking, billing

### Patient Management
- Register patients with phone-based deduplication
- Search across 10,000+ patients with real-time filtering
- Paginated patient list
- Full patient profile with visit history (doctor/admin only)

### Appointment Scheduling
- Book appointments with cascading dropdowns (department → doctor → date → available slots)
- 30-minute slot system, 9 AM to 5 PM
- Double-layered conflict detection (application + database constraint)
- Status transitions with role enforcement:
  - `scheduled → in_progress` (doctor only)
  - `scheduled → cancelled / no_show` (front desk, admin)
  - `in_progress → completed` (doctor only)

### Clinical Documentation
- Doctors write visit notes: symptoms, diagnosis, ICD-10 code, prescription, follow-up
- Visit creation auto-completes the appointment and auto-creates a billing record

### Billing
- Auto-generated consultation fee invoice on visit creation
- Front desk adds test/procedure line items
- Total recalculates on every change
- Payment processing: cash, card, UPI, insurance
- Invoice history with status filtering (pending/paid/partially paid/waived)

### Admin Dashboard
- Today's appointments breakdown
- Today's revenue
- Pending payment summary
- 30-day revenue chart (consultation vs tests/procedures)
- Department performance table

---

## Data Model

9 PostgreSQL tables:

```
users
departments         ← consultation_fee is department-level (Indian polyclinic model)
doctors             ← linked 1-to-1 with users
patients            ← phone is primary dedup key
appointments        ← unique constraint on (doctor_id, date, time)
visits              ← one per appointment, auto-creates billing
billing_records     ← invoice header
billing_items       ← line items (consultation fee + tests/procedures)
patient_documents   ← file metadata (filesystem storage)
```

---

## Local Development

### Prerequisites
- Python 3.12+
- PostgreSQL 15
- Node.js 18+

### Backend Setup

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
```

```bash
createdb redmond_pms
export FLASK_APP=run.py
flask db upgrade
python seed.py
flask run --port 8000
```

### Frontend Setup

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

### Optional: Generate Synthetic Data

```bash
cd backend
python generate_data.py
```

Generates 10,000 patients, ~22,000 appointments, ~12,000 visits with realistic Indian names, weighted blood group distributions, and 2 years of billing history.

---

## API Overview

```
POST   /api/v1/auth/login
GET    /api/v1/auth/me

GET    /api/v1/patients?search=&page=&per_page=
POST   /api/v1/patients
GET    /api/v1/patients/:id
PUT    /api/v1/patients/:id
GET    /api/v1/patients/check-phone/:phone
GET    /api/v1/patients/:id/visits

GET    /api/v1/departments
GET    /api/v1/doctors?department_id=
GET    /api/v1/doctors/:id/available-slots?date=

GET    /api/v1/appointments/today
POST   /api/v1/appointments
PATCH  /api/v1/appointments/:id/status

POST   /api/v1/visits
GET    /api/v1/visits/:id

GET    /api/v1/billing
GET    /api/v1/billing/:id
POST   /api/v1/billing/:id/items
DELETE /api/v1/billing/:id/items/:item_id
PATCH  /api/v1/billing/:id/pay

GET    /api/v1/dashboard/summary
GET    /api/v1/dashboard/revenue?period=30days
GET    /api/v1/dashboard/department-stats
GET    /api/v1/dashboard/doctor-utilization
```

---

## Performance

Query performance verified with `EXPLAIN ANALYZE` on 10,000+ patients and 22,000+ appointments:

| Query | Index Used | Time |
|-------|-----------|------|
| Patient phone lookup | `ix_patients_phone` | 0.13ms |
| Doctor schedule | `ix_appointments_doctor_date` | 0.10ms |

8 custom indexes beyond PKs and unique constraints — composite indexes for high-frequency query patterns.

---

## Architecture Decisions

**Consultation fee on Department, not Doctor** — Indian polyclinics charge by department. All cardiologists charge the same Cardiology fee regardless of seniority.

**Phone as patient dedup key** — patients in Tier 2 Indian cities reliably have mobile numbers. Email is optional.

**Auto-billing on visit creation** — single transaction creates visit, marks appointment completed, creates invoice with consultation fee. If any step fails, everything rolls back.

**File storage abstraction** — `save_file()`, `get_absolute_path()`, `delete_file()` in `utils/file_storage.py`. Swapping to S3 means replacing one file. Uses UUID filenames to prevent collisions and path traversal attacks.

**Belt-and-suspenders conflict detection** — appointment booking checks for conflicts at the application layer (human-readable error) and catches `IntegrityError` from the DB unique constraint (race condition protection).

---

## Project Structure

```
pms/
├── backend/
│   ├── app/
│   │   ├── models/          # 9 SQLAlchemy models
│   │   ├── routes/          # 8 Blueprint route groups
│   │   ├── services/        # Business logic layer
│   │   ├── schemas/         # Marshmallow validation
│   │   └── utils/           # Decorators, helpers, file storage
│   ├── migrations/          # Alembic migration files
│   ├── seed.py              # Base seed data
│   ├── generate_data.py     # 10k synthetic patient generator
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/             # JWT-aware fetch wrapper
        ├── context/         # Auth context (global state)
        ├── components/
        │   ├── auth/        # Login page
        │   ├── common/      # Navbar, ProtectedRoute
        │   ├── dashboard/   # Dashboard + RevenueChart
        │   ├── patients/    # List, Form, Profile
        │   ├── appointments/ # TodaySchedule, BookAppointment
        │   ├── visits/      # VisitForm
        │   └── billing/     # BillingList, InvoiceDetail
        └── App.js           # Router + auth wrapper
```

---

## Built By

Satyabrat Srikumar & Arth Singh — Columbia University MS in Computer Science  
Built as a portfolio project demonstrating full-stack ML engineering capabilities.

-- pipeline/sql/create_schema.sql
-- Creates analytics schema and all destination tables.
-- Safe to run multiple times (IF NOT EXISTS throughout).

CREATE SCHEMA IF NOT EXISTS analytics;

-- Pipeline run log — every job logs here
CREATE TABLE IF NOT EXISTS analytics.pipeline_runs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds NUMERIC(10,2),
    rows_processed INTEGER DEFAULT 0,
    error_message TEXT
);

-- Denormalized patient profiles with aggregated metrics
CREATE TABLE IF NOT EXISTS analytics.patient_profiles (
    patient_id INTEGER PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    age INTEGER,
    gender VARCHAR(20),
    blood_group VARCHAR(10),
    phone VARCHAR(20),
    total_visits INTEGER DEFAULT 0,
    first_visit_date DATE,
    last_visit_date DATE,
    visit_frequency_days NUMERIC(10,2),
    total_billed NUMERIC(12,2) DEFAULT 0,
    total_paid NUMERIC(12,2) DEFAULT 0,
    outstanding_balance NUMERIC(12,2) DEFAULT 0,
    total_appointments INTEGER DEFAULT 0,
    no_show_count INTEGER DEFAULT 0,
    no_show_rate NUMERIC(5,2) DEFAULT 0,
    primary_department VARCHAR(100),
    primary_doctor VARCHAR(255),
    risk_flags TEXT[],
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Per-patient clinical summaries (RAG input)
CREATE TABLE IF NOT EXISTS analytics.patient_clinical_summaries (
    patient_id INTEGER PRIMARY KEY,
    summary_text TEXT NOT NULL,
    visit_count INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,
    summary_hash VARCHAR(64),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Daily revenue rollups by department
CREATE TABLE IF NOT EXISTS analytics.daily_revenue (
    date DATE NOT NULL,
    department_id INTEGER NOT NULL,
    department_name VARCHAR(100),
    consultation_revenue NUMERIC(12,2) DEFAULT 0,
    test_revenue NUMERIC(12,2) DEFAULT 0,
    procedure_revenue NUMERIC(12,2) DEFAULT 0,
    other_revenue NUMERIC(12,2) DEFAULT 0,
    total_revenue NUMERIC(12,2) DEFAULT 0,
    paid_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (date, department_id)
);

-- Appointment funnel metrics per doctor per day
CREATE TABLE IF NOT EXISTS analytics.operational_metrics (
    date DATE NOT NULL,
    doctor_id INTEGER NOT NULL,
    department_id INTEGER,
    department_name VARCHAR(100),
    doctor_name VARCHAR(255),
    total_slots INTEGER DEFAULT 16,
    booked_slots INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    cancelled INTEGER DEFAULT 0,
    no_show INTEGER DEFAULT 0,
    utilization_rate NUMERIC(5,2) DEFAULT 0,
    completion_rate NUMERIC(5,2) DEFAULT 0,
    no_show_rate NUMERIC(5,2) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (date, doctor_id)
);
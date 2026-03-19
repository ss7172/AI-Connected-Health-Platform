-- pipeline/sql/revenue_analytics.sql
-- Pre-computes daily revenue by department with category breakdown.
-- Replaces real-time aggregation queries on the PMS dashboard.
-- UPSERT: safe to re-run, updates existing rows.

INSERT INTO analytics.daily_revenue (
    date,
    department_id,
    department_name,
    consultation_revenue,
    test_revenue,
    procedure_revenue,
    other_revenue,
    total_revenue,
    paid_count,
    pending_count,
    last_updated
)
SELECT
    DATE(br.payment_date)                                           AS date,
    d.id                                                            AS department_id,
    d.name                                                          AS department_name,
    COALESCE(SUM(bi.amount) FILTER (WHERE bi.category = 'consultation'), 0) AS consultation_revenue,
    COALESCE(SUM(bi.amount) FILTER (WHERE bi.category = 'test'), 0)         AS test_revenue,
    COALESCE(SUM(bi.amount) FILTER (WHERE bi.category = 'procedure'), 0)    AS procedure_revenue,
    COALESCE(SUM(bi.amount) FILTER (WHERE bi.category = 'other'), 0)        AS other_revenue,
    COALESCE(SUM(bi.amount), 0)                                    AS total_revenue,
    COUNT(DISTINCT br.id) FILTER (WHERE br.status = 'paid')        AS paid_count,
    COUNT(DISTINCT br.id) FILTER (WHERE br.status = 'pending')     AS pending_count,
    NOW()                                                           AS last_updated
FROM billing_records br
JOIN billing_items bi      ON bi.billing_record_id = br.id
JOIN visits v              ON v.id = br.visit_id
JOIN appointments a        ON a.id = v.appointment_id
JOIN departments d         ON d.id = a.department_id
WHERE br.payment_date IS NOT NULL
GROUP BY DATE(br.payment_date), d.id, d.name
ON CONFLICT (date, department_id) DO UPDATE SET
    department_name       = EXCLUDED.department_name,
    consultation_revenue  = EXCLUDED.consultation_revenue,
    test_revenue          = EXCLUDED.test_revenue,
    procedure_revenue     = EXCLUDED.procedure_revenue,
    other_revenue         = EXCLUDED.other_revenue,
    total_revenue         = EXCLUDED.total_revenue,
    paid_count            = EXCLUDED.paid_count,
    pending_count         = EXCLUDED.pending_count,
    last_updated          = NOW();
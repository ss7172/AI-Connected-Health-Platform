-- pipeline/sql/operational_metrics.sql
-- Pre-computes appointment funnel metrics per doctor per day.
-- Replaces the N+1 doctor-utilization endpoint on the dashboard.
-- Total slots = 16 per day (9AM-5PM, 30-min intervals).

INSERT INTO analytics.operational_metrics (
    date,
    doctor_id,
    department_id,
    department_name,
    doctor_name,
    total_slots,
    booked_slots,
    completed,
    cancelled,
    no_show,
    utilization_rate,
    completion_rate,
    no_show_rate,
    last_updated
)
SELECT
    a.appointment_date                                          AS date,
    d.id                                                        AS doctor_id,
    dep.id                                                      AS department_id,
    dep.name                                                    AS department_name,
    u.full_name                                                 AS doctor_name,
    16                                                          AS total_slots,
    COUNT(*)                                                    AS booked_slots,
    COUNT(*) FILTER (WHERE a.status = 'completed')              AS completed,
    COUNT(*) FILTER (WHERE a.status = 'cancelled')              AS cancelled,
    COUNT(*) FILTER (WHERE a.status = 'no_show')               AS no_show,
    ROUND(COUNT(*) * 100.0 / 16, 2)                            AS utilization_rate,
    ROUND(
        COUNT(*) FILTER (WHERE a.status = 'completed') * 100.0
        / NULLIF(COUNT(*) FILTER (WHERE a.status != 'cancelled'), 0)
    , 2)                                                        AS completion_rate,
    ROUND(
        COUNT(*) FILTER (WHERE a.status = 'no_show') * 100.0
        / NULLIF(COUNT(*), 0)
    , 2)                                                        AS no_show_rate,
    NOW()                                                       AS last_updated
FROM appointments a
JOIN doctors d      ON d.id = a.doctor_id
JOIN users u        ON u.id = d.user_id
JOIN departments dep ON dep.id = a.department_id
GROUP BY
    a.appointment_date,
    d.id,
    dep.id,
    dep.name,
    u.full_name
ON CONFLICT (date, doctor_id) DO UPDATE SET
    department_id    = EXCLUDED.department_id,
    department_name  = EXCLUDED.department_name,
    doctor_name      = EXCLUDED.doctor_name,
    total_slots      = EXCLUDED.total_slots,
    booked_slots     = EXCLUDED.booked_slots,
    completed        = EXCLUDED.completed,
    cancelled        = EXCLUDED.cancelled,
    no_show          = EXCLUDED.no_show,
    utilization_rate = EXCLUDED.utilization_rate,
    completion_rate  = EXCLUDED.completion_rate,
    no_show_rate     = EXCLUDED.no_show_rate,
    last_updated     = NOW();
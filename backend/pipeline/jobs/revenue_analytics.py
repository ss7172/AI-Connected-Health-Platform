# pipeline/jobs/revenue_analytics.py
"""
Revenue analytics job.
Pre-computes daily revenue by department with consultation/test/procedure breakdown.
Replaces real-time aggregation queries on the PMS dashboard.
"""
from pipeline.jobs.base import BaseJob
from pipeline.db import get_connection, load_sql
from sqlalchemy import text


class RevenueAnalyticsJob(BaseJob):
    """
    Transforms billing_records + billing_items into analytics.daily_revenue.

    Source: billing_records JOIN billing_items JOIN visits JOIN appointments JOIN departments
    Destination: analytics.daily_revenue
    Granularity: one row per department per day
    """
    job_name = 'revenue_analytics'

    def run(self) -> int:
        """
        Execute revenue analytics SQL and return rows upserted.

        Returns:
            Number of rows processed
        """
        sql = load_sql('revenue_analytics.sql')

        with get_connection() as conn:
            result = conn.execute(text(sql))
            conn.commit()
            return result.rowcount
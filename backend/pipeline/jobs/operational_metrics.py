# pipeline/jobs/operational_metrics.py
"""
Operational metrics job.
Pre-computes appointment funnel metrics per doctor per day.
Replaces N+1 doctor-utilization queries on the dashboard.
"""
from pipeline.jobs.base import BaseJob
from pipeline.db import get_connection, load_sql
from sqlalchemy import text


class OperationalMetricsJob(BaseJob):
    """
    Transforms appointments into analytics.operational_metrics.

    Source: appointments JOIN doctors JOIN users JOIN departments
    Destination: analytics.operational_metrics
    Granularity: one row per doctor per day
    """
    job_name = 'operational_metrics'

    def run(self) -> int:
        """
        Execute operational metrics SQL and return rows upserted.

        Returns:
            Number of rows processed
        """
        sql = load_sql('operational_metrics.sql')

        with get_connection() as conn:
            result = conn.execute(text(sql))
            conn.commit()
            return result.rowcount
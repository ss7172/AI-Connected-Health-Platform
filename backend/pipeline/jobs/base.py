# pipeline/jobs/base.py
"""
Base job class. Handles pipeline_runs logging automatically.
Every job inherits from BaseJob and implements run().
"""
import time
import traceback
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from pipeline.db import get_connection


class BaseJob:
    """
    Base class for all pipeline jobs.

    Subclasses must implement:
        job_name: str class attribute
        run() -> int: executes the job, returns rows processed
    """
    job_name: str = 'base'

    def execute(self) -> dict:
        """
        Wraps run() with timing and pipeline_runs logging.
        Call this from the runner, not run() directly.

        Returns:
            Dict with status, rows_processed, duration_seconds
        """
        run_id = self._log_start()
        started = time.time()

        try:
            rows = self.run()
            duration = round(time.time() - started, 2)
            self._log_success(run_id, rows, duration)
            print(f"  ✓ {self.job_name}: {rows} rows in {duration}s")
            return {
                'status': 'success',
                'rows_processed': rows,
                'duration_seconds': duration,
            }
        except Exception as e:
            duration = round(time.time() - started, 2)
            error = traceback.format_exc()
            self._log_failure(run_id, error, duration)
            print(f"  ✗ {self.job_name}: FAILED after {duration}s")
            print(f"    {str(e)}")
            raise

    def run(self) -> int:
        """
        Execute the job logic.
        Must be implemented by subclasses.

        Returns:
            Number of rows processed
        """
        raise NotImplementedError(f"{self.job_name}.run() not implemented")

    def _log_start(self) -> int:
        """Insert a pipeline_runs row with status=running. Returns run ID."""
        with get_connection() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO analytics.pipeline_runs
                        (job_name, status, started_at)
                    VALUES
                        (:job_name, 'running', NOW())
                    RETURNING id
                """),
                {'job_name': self.job_name}
            )
            run_id = result.fetchone()[0]
            conn.commit()
        return run_id

    def _log_success(self, run_id: int, rows: int, duration: float) -> None:
        """Update pipeline_runs row with success status."""
        with get_connection() as conn:
            conn.execute(
                text("""
                    UPDATE analytics.pipeline_runs
                    SET status = 'success',
                        completed_at = NOW(),
                        duration_seconds = :duration,
                        rows_processed = :rows
                    WHERE id = :run_id
                """),
                {'run_id': run_id, 'rows': rows, 'duration': duration}
            )
            conn.commit()

    def _log_failure(self, run_id: int, error: str, duration: float) -> None:
        """Update pipeline_runs row with failed status and error message."""
        with get_connection() as conn:
            conn.execute(
                text("""
                    UPDATE analytics.pipeline_runs
                    SET status = 'failed',
                        completed_at = NOW(),
                        duration_seconds = :duration,
                        error_message = :error
                    WHERE id = :run_id
                """),
                {'run_id': run_id, 'error': error[:2000], 'duration': duration}
            )
            conn.commit()
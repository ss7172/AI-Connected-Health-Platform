# pipeline/runner.py
"""
Pipeline CLI runner.
Usage:
    python -m pipeline.runner revenue_analytics
    python -m pipeline.runner operational_metrics
    python -m pipeline.runner patient_analytics
    python -m pipeline.runner clinical_summaries
    python -m pipeline.runner all
"""
import sys
import time
from datetime import datetime


def get_jobs() -> dict:
    """Registry of all available jobs."""
    from pipeline.jobs.revenue_analytics import RevenueAnalyticsJob
    from pipeline.jobs.operational_metrics import OperationalMetricsJob
    return {
        'revenue_analytics': RevenueAnalyticsJob,
        'operational_metrics': OperationalMetricsJob,
    }


def run_job(job_name: str) -> None:
    """Run a single job by name."""
    jobs = get_jobs()
    if job_name not in jobs:
        print(f"Unknown job: {job_name}")
        print(f"Available jobs: {list(jobs.keys())}")
        sys.exit(1)

    job = jobs[job_name]()
    job.execute()


def run_all() -> None:
    """Run all jobs in dependency order."""
    jobs = get_jobs()
    print(f"\n{'='*50}")
    print(f"Pipeline run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    started = time.time()
    failed = []

    for job_name, job_class in jobs.items():
        print(f"\nRunning: {job_name}")
        try:
            job_class().execute()
        except Exception as e:
            failed.append(job_name)

    duration = round(time.time() - started, 2)
    print(f"\n{'='*50}")
    print(f"Pipeline completed in {duration}s")
    if failed:
        print(f"Failed jobs: {failed}")
    else:
        print("All jobs succeeded.")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.runner <job_name|all>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'all':
        run_all()
    else:
        run_job(command)
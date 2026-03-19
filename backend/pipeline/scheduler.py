# pipeline/scheduler.py
"""
APScheduler configuration for nightly pipeline runs.
Runs at 2 AM daily in production.
On Render free tier, won't persist across restarts —
use POST /api/v1/pipeline/run for manual triggers.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()


def run_all_jobs() -> None:
    """Run all pipeline jobs in order. Called by scheduler."""
    from pipeline.runner import run_all
    run_all()


def start_scheduler() -> None:
    """
    Start the background scheduler.
    Adds nightly 2AM cron job.
    Called from Flask app factory on startup.
    """
    scheduler.add_job(
        run_all_jobs,
        CronTrigger(hour=2, minute=0),
        id='nightly_pipeline',
        replace_existing=True,
    )
    scheduler.start()
    print("Pipeline scheduler started — nightly run at 2:00 AM")


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
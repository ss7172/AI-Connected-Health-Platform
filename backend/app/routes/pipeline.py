# app/routes/pipeline.py
"""
Pipeline management API endpoints.
POST /api/v1/pipeline/run    — trigger all jobs manually (admin only)
GET  /api/v1/pipeline/status — last run per job (admin only)
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from app.extensions import db
from app.utils.decorators import role_required
from app.utils.helpers import success_response, error_response

pipeline_bp = Blueprint('pipeline', __name__)


@pipeline_bp.route('/run', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def run_pipeline():
    """
    Trigger full pipeline run manually.
    POST /api/v1/pipeline/run
    admin only.
    """
    try:
        from pipeline.runner import run_all
        run_all()
        return success_response({'message': 'Pipeline run completed successfully'}, 200)
    except Exception as e:
        return error_response(f"Pipeline failed: {str(e)}", 500)


@pipeline_bp.route('/status', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def pipeline_status():
    """
    Get last run status per job.
    GET /api/v1/pipeline/status
    admin only.
    """
    sql = text("""
        SELECT DISTINCT ON (job_name)
            job_name,
            status,
            started_at,
            completed_at,
            duration_seconds,
            rows_processed,
            error_message
        FROM analytics.pipeline_runs
        ORDER BY job_name, started_at DESC
    """)

    result = db.session.execute(sql)
    rows = [dict(r._mapping) for r in result]

    for row in rows:
        if row['started_at']:
            row['started_at'] = row['started_at'].isoformat()
        if row['completed_at']:
            row['completed_at'] = row['completed_at'].isoformat()

    return success_response({'jobs': rows}, 200)